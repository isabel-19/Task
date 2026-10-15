import io
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, Response, JSONResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import Field
from starlette.datastructures import UploadFile
from . import models as m
from .config import settings
from .db import get_db
from .security import current_user, require
from .service import get_record
from .task_policy import require_participant
from .task_routes import StrictInput, AdvanceInput, expected_revision, record_advance
from .evidence_storage import store_upload, document_preview_bytes, validate_content, clean_name, TYPES
from .evidence_objects import discard_object
from .cloud_accounts import public_accounts, start_connection, finish_connection, access_token, disconnect
from .cloud_files import list_microsoft_files, download_file
from .cloud_configuration import values, public_configuration, save_configuration

router = APIRouter()


class ConfigurationInput(StrictInput):
    revision: int = Field(ge=0)
    cloud_public_api_url: str | None = Field(default=None, max_length=500)
    cloud_frontend_url: str | None = Field(default=None, max_length=500)
    google_client_id: str | None = Field(default=None, max_length=500)
    google_client_secret: str | None = Field(default=None, max_length=2000)
    google_picker_api_key: str | None = Field(default=None, max_length=500)
    google_project_number: str | None = Field(default=None, max_length=30)
    microsoft_client_id: str | None = Field(default=None, max_length=500)
    microsoft_client_secret: str | None = Field(default=None, max_length=2000)
    microsoft_tenant: str | None = Field(default=None, max_length=253)


@router.get('/cloud/configuration')
def configuration(user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'admin.write')
    return public_configuration(db)


@router.post('/cloud/configuration')
def configure(body: ConfigurationInput, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'admin.write')
    return save_configuration(db, user, body.revision, body.model_dump(exclude={'revision'}, exclude_unset=True))


@router.get('/cloud/accounts')
def accounts(user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'tasks.read')
    return {'items': public_accounts(db, user)}


@router.post('/cloud/{provider}/connect')
def connect(provider: str, request: Request, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'tasks.write')
    return {'authorization_url': start_connection(db, user, provider, request.cookies.get('ogc_session', ''))}


@router.get('/cloud/{provider}/callback')
def callback(provider: str, request: Request, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'tasks.write')
    query = getattr(request.state, 'oauth_query', request.query_params)
    try:
        connected = finish_connection(db, user, provider, request.cookies.get('ogc_session', ''), query)
        status = 'connected' if connected else 'cancelled'
    except HTTPException as error:
        if error.status_code < 500:
            raise
        status = 'failed'
    return RedirectResponse(values(db)['cloud_frontend_url'].rstrip('/') + '/cuentas?provider=' + provider + '&status=' + status, status_code=303)


@router.post('/cloud/{provider}/disconnect')
def unlink(provider: str, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'tasks.read')
    disconnect(db, user, provider)
    return {'ok': True}


@router.post('/cloud/google/picker')
def google_picker(user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'tasks.write')
    token = access_token(db, user, 'google')
    config = values(db)
    return {'access_token': token, 'api_key': config['google_picker_api_key'], 'app_id': config['google_project_number']}


class GooglePreviewInput(StrictInput):
    item_id: str = Field(min_length=1, max_length=256)


@router.post('/cloud/google/preview')
def google_preview(body: GooglePreviewInput, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'tasks.write')
    downloaded = download_file('google', access_token(db, user, 'google'), body.item_id)
    name = clean_name(downloaded['name'])
    suffix = Path(name).suffix.lower()
    validate_content(downloaded['data'], suffix)
    headers = {'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
               'Content-Security-Policy': "default-src 'none'; sandbox"}
    if suffix == '.pdf' or TYPES[suffix].startswith('image/'):
        return Response(downloaded['data'], media_type=TYPES[suffix], headers=headers)
    return JSONResponse(document_preview_bytes(downloaded['data'], name), headers=headers)


@router.get('/cloud/microsoft/files')
def microsoft_files(folder: str | None = None, cursor: str | None = None, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'tasks.write')
    return list_microsoft_files(access_token(db, user, 'microsoft'), user.id, folder, cursor)


class CloudAdvanceInput(StrictInput):
    revision: int
    progress: int = Field(ge=0, le=100)
    comment: str = Field(min_length=1, max_length=5000)
    provider: str
    item_id: str = Field(min_length=1, max_length=256)


@router.post('/tasks/{identifier}/advance-cloud')
async def advance_cloud(identifier: str, body: CloudAdvanceInput, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'tasks.write')
    task = get_record(db, m.Task, identifier)
    require_participant(db, user, task)
    expected_revision(task, body.revision)
    if body.provider not in {'google', 'microsoft'}:
        raise HTTPException(422, 'Selecciona Google o Microsoft.')
    if not settings.evidence_uploads_enabled:
        raise HTTPException(503, 'Esta instalación no tiene habilitado el almacenamiento de archivos de evidencia.')
    token = access_token(db, user, body.provider)
    downloaded = await run_in_threadpool(download_file, body.provider, token, body.item_id)
    stored = None
    try:
        # Refresh after the download: another teammate may have updated the task.
        db.expire_all()
        expected_revision(get_record(db, m.Task, identifier, True), body.revision)
        stored = await store_upload(UploadFile(io.BytesIO(downloaded['data']), filename=downloaded['name']))
        stored.update(source_provider=body.provider, source_item_id=body.item_id, source_url=downloaded['source'])
        return record_advance(identifier, AdvanceInput(revision=body.revision, progress=body.progress, comment=body.comment), user, db, uploaded=stored)
    except Exception:
        db.rollback()
        if stored:
            await discard_object(stored['storage_key'])
        raise
