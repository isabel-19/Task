"""Read selected cloud files, export native Docs and bound downloads before storage."""
import re
import time
from pathlib import Path
from urllib.parse import quote, urlparse
import httpx
from fastapi import HTTPException
from .evidence_storage import upload_limit, TYPES, SIZE_MESSAGE
from .cloud_accounts import encrypt, decrypt

GOOGLE = 'https://www.googleapis.com/drive/v3/files/'
GRAPH = 'https://graph.microsoft.com/v1.0/me/drive/'
EXPORTS = {
    'application/vnd.google-apps.document': ('.pdf', 'application/pdf'),
    'application/vnd.google-apps.presentation': ('.pdf', 'application/pdf'),
    'application/vnd.google-apps.spreadsheet': ('.xlsx', TYPES['.xlsx']),
}


def http_client():
    return httpx.Client(timeout=40, follow_redirects=False)


def identifier(value):
    if not re.fullmatch(r'[a-zA-Z0-9!_.-]{1,256}', value or '') or value in {'.', '..'}:
        raise HTTPException(422, 'Selecciona un documento válido.')
    return quote(value, safe='')


def provider_error(response):
    if response.status_code in {401, 403}:
        raise HTTPException(409, 'La cuenta no permite abrir este documento. Vuelve a vincularla o elige otro archivo.')
    if response.status_code == 404:
        raise HTTPException(404, 'El documento ya no está disponible en la cuenta vinculada.')
    if response.status_code == 429:
        raise HTTPException(429, 'El servicio de documentos está ocupado. Intenta nuevamente en unos minutos.')
    if response.status_code >= 400:
        raise HTTPException(502, 'No se pudo consultar el documento en el servicio de origen.')


def safe_source(url):
    value = urlparse(url or '')
    if value.scheme != 'https' or not value.hostname or value.username or value.password:
        raise HTTPException(502, 'El servicio devolvió un enlace de documento no válido.')
    return url


def remote_json(client, url, token, params=None):
    response = client.get(url, headers={'Authorization': 'Bearer ' + token}, params=params)
    provider_error(response)
    return response.json()


def list_microsoft_files(token, user_id, folder=None, cursor=None):
    try:
        if cursor:
            saved = decrypt(cursor)
            if saved.get('user') != user_id or saved.get('folder') != (folder or '') or saved.get('expires', 0) < time.time():
                raise HTTPException(422, 'Actualiza el listado para seguir consultando documentos.')
            url = saved['url']
            parsed = urlparse(url)
            if parsed.scheme != 'https' or parsed.netloc != 'graph.microsoft.com' or not parsed.path.startswith('/v1.0/me/drive/'):
                raise HTTPException(422, 'Página de documentos no válida.')
            params = None
        else:
            url = GRAPH + ('items/' + identifier(folder) if folder else 'root') + '/children'
            params = {'$top': '50', '$select': 'id,name,size,file,folder,webUrl,lastModifiedDateTime', '$orderby': 'name'}
        with http_client() as client:
            response = remote_json(client, url, token, params)
        items = [{'id': row['id'], 'name': row['name'], 'folder': 'folder' in row,
                  'size': row.get('size', 0), 'url': safe_source(row['webUrl']) if row.get('webUrl') else None,
                  'supported': 'folder' in row or Path(row['name']).suffix.lower() in TYPES}
                 for row in response.get('value', [])]
        next_url = response.get('@odata.nextLink')
        next_cursor = encrypt({'user': user_id, 'folder': folder or '', 'url': next_url, 'expires': time.time() + 900}) if next_url else None
        return {'items': items, 'next_cursor': next_cursor}
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise HTTPException(502, 'No se pudo consultar OneDrive. Intenta nuevamente.')


def bounded_download(client, url, token=None, params=None):
    headers = {'Authorization': 'Bearer ' + token} if token else {}
    with client.stream('GET', url, headers=headers, params=params) as response:
        if response.status_code in {301, 302, 303, 307, 308}:
            # Graph supplies a short-lived download URL. Never forward the OAuth
            # header to that host, and accept redirects only to Microsoft hosts.
            target = response.headers.get('location', '')
            parsed = urlparse(safe_source(target))
            allowed = ('sharepoint.com', '1drv.com', 'onedrive.com', 'livefilestore.com', 'storage.live.com')
            if not any(parsed.hostname == host or parsed.hostname.endswith('.' + host) for host in allowed):
                raise HTTPException(502, 'El servicio devolvió una descarga no admitida.')
            if not token:
                raise HTTPException(502, 'La descarga del documento tiene demasiadas redirecciones.')
            return bounded_download(client, target)
        provider_error(response)
        try:
            length = int(response.headers.get('content-length', '0'))
        except ValueError:
            length = 0
        if length > upload_limit():
            raise HTTPException(413, SIZE_MESSAGE)
        data = bytearray()
        for chunk in response.iter_bytes(65536):
            if len(data) + len(chunk) > upload_limit():
                raise HTTPException(413, SIZE_MESSAGE)
            data.extend(chunk)
        return bytes(data)


def download_file(provider, token, item_id):
    try:
        remote_id = identifier(item_id)
        with http_client() as client:
            if provider == 'google':
                metadata = remote_json(client, GOOGLE + remote_id, token, {'fields': 'id,name,mimeType,size,webViewLink,trashed,capabilities(canDownload)', 'supportsAllDrives': 'true'})
                if metadata.get('trashed') or metadata.get('capabilities', {}).get('canDownload') is False:
                    raise HTTPException(403, 'El propietario no permite descargar o copiar este documento. Puedes abrirlo en Google con tu cuenta.')
                source = safe_source(metadata.get('webViewLink') or 'https://drive.google.com/file/d/' + remote_id + '/view')
                if metadata.get('mimeType') in EXPORTS:
                    suffix, mime = EXPORTS[metadata['mimeType']]
                    name = metadata['name'] + suffix
                    data = bounded_download(client, GOOGLE + remote_id + '/export', token, {'mimeType': mime})
                else:
                    name = metadata['name']
                    if Path(name).suffix.lower() not in TYPES:
                        raise HTTPException(422, 'El formato de este archivo no está admitido como evidencia.')
                    if int(metadata.get('size', 0)) > upload_limit():
                        raise HTTPException(413, SIZE_MESSAGE)
                    data = bounded_download(client, GOOGLE + remote_id, token, {'alt': 'media', 'supportsAllDrives': 'true'})
            else:
                metadata = remote_json(client, GRAPH + 'items/' + remote_id, token,
                                       {'$select': 'id,name,size,file,webUrl'})
                if 'file' not in metadata:
                    raise HTTPException(422, 'Selecciona un archivo, no una carpeta.')
                name = metadata['name']
                source = safe_source(metadata['webUrl'])
                if Path(name).suffix.lower() not in TYPES:
                    raise HTTPException(422, 'El formato de este archivo no está admitido como evidencia.')
                if metadata.get('size', 0) > upload_limit():
                    raise HTTPException(413, SIZE_MESSAGE)
                data = bounded_download(client, GRAPH + 'items/' + remote_id + '/content', token)
        return {'name': name, 'data': data, 'source': source}
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise HTTPException(502, 'No se pudo obtener el archivo de la cuenta vinculada. Intenta nuevamente.')
