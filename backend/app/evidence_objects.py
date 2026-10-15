"""Private evidence objects: local development or Supabase Storage for free hosting."""
import hashlib
import logging
import re
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from fastapi import HTTPException
from .config import settings

logger = logging.getLogger(__name__)
UNAVAILABLE = 'El archivo no está disponible. Comunícalo a jefatura.'
STORAGE_ERROR = 'El almacenamiento de evidencias no está disponible. Intenta nuevamente.'
MAX_BYTES = 50 * 1024 * 1024


def checked_key(key):
    if not re.fullmatch(r'[a-f0-9]{32}', key):
        raise HTTPException(404, 'Archivo no encontrado.')
    return key


def stored_path(key):
    root = Path(settings.evidence_storage_dir).resolve() if settings.evidence_storage_dir else Path(__file__).resolve().parents[1] / 'storage/evidence'
    return root / checked_key(key)


def remote_config():
    if settings.evidence_storage_backend != 'supabase':
        raise HTTPException(503, STORAGE_ERROR)
    url = urlsplit(settings.supabase_url)
    bucket = settings.supabase_storage_bucket
    secret = settings.supabase_service_key.get_secret_value()
    if (url.scheme != 'https' or not re.fullmatch(r'[a-z0-9-]+\.supabase\.co', url.netloc)
            or url.path not in ('', '/') or url.query or url.fragment
            or not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,62}', bucket) or not secret):
        raise HTTPException(503, STORAGE_ERROR)
    headers = {'apikey': secret}
    if not secret.startswith('sb_secret_'):
        # Legacy service_role keys are JWTs; new secret keys use apikey only.
        headers['Authorization'] = 'Bearer ' + secret
    return settings.supabase_url.rstrip('/') + '/storage/v1', bucket, headers


def check_private_bucket(response):
    try:
        valid = response.is_success and response.json().get('public') is False
    except (ValueError, AttributeError):
        valid = False
    if not valid:
        raise HTTPException(503, STORAGE_ERROR)


async def put_object(key, data, content_type):
    checked_key(key)
    if settings.evidence_storage_backend == 'local':
        path = stored_path(key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(data)
        except OSError:
            raise HTTPException(503, STORAGE_ERROR) from None
        return
    base, bucket, headers = remote_config()
    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=False) as client:
            check_private_bucket(await client.get(f'{base}/bucket/{bucket}', headers=headers))
            response = await client.post(f'{base}/object/{bucket}/{key}', content=data,
                                         headers={**headers, 'Content-Type': content_type, 'x-upsert': 'false'})
            if not response.is_success:
                raise HTTPException(503, STORAGE_ERROR)
    except httpx.HTTPError:
        raise HTTPException(503, STORAGE_ERROR) from None


async def discard_object(key):
    """Best-effort compensation for an upload whose DB transaction failed."""
    checked_key(key)
    try:
        if settings.evidence_storage_backend == 'local':
            stored_path(key).unlink(missing_ok=True)
        else:
            base, bucket, headers = remote_config()
            async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
                response = await client.delete(f'{base}/object/{bucket}/{key}', headers=headers)
                if not response.is_success and response.status_code != 404:
                    raise HTTPException(503, STORAGE_ERROR)
    except (OSError, httpx.HTTPError, HTTPException):
        # No provider payload, secret or filename is written to logs.
        logger.warning('No se pudo limpiar un archivo de una entrega fallida; requiere conciliación de almacenamiento.')


def read_object(file):
    checked_key(file.storage_key)
    if not 0 < file.byte_size <= MAX_BYTES:
        raise HTTPException(404, UNAVAILABLE)
    if settings.evidence_storage_backend == 'local':
        path = stored_path(file.storage_key)
        try:
            if path.stat().st_size != file.byte_size:
                raise HTTPException(404, UNAVAILABLE)
            data = path.read_bytes()
        except OSError:
            raise HTTPException(404, UNAVAILABLE) from None
    else:
        base, bucket, headers = remote_config()
        try:
            with httpx.Client(timeout=60, follow_redirects=False) as client:
                check_private_bucket(client.get(f'{base}/bucket/{bucket}', headers=headers))
                with client.stream('GET', f'{base}/object/authenticated/{bucket}/{file.storage_key}', headers=headers) as response:
                    if response.status_code == 404:
                        raise HTTPException(404, UNAVAILABLE)
                    if not response.is_success:
                        raise HTTPException(503, STORAGE_ERROR)
                    data = bytearray()
                    for chunk in response.iter_bytes():
                        data.extend(chunk)
                        if len(data) > file.byte_size:
                            raise HTTPException(404, UNAVAILABLE)
                    data = bytes(data)
        except httpx.HTTPError:
            raise HTTPException(503, STORAGE_ERROR) from None
    if len(data) != file.byte_size or hashlib.sha256(data).hexdigest() != file.sha256:
        raise HTTPException(404, UNAVAILABLE)
    return data
