"""Authenticated access to evidence files; no publicly mounted storage folder."""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from urllib.parse import quote
from sqlalchemy import select
from . import models as m
from .db import get_db
from .security import current_user, require
from .task_policy import visible_tasks, team_reader
from .service import get_record
from .evidence_storage import document_preview_bytes
from .evidence_objects import read_object

router = APIRouter()


def accessible_file(db, user, identifier):
    require(db, user, 'tasks.read')
    file = get_record(db, m.EvidenceFile, identifier)
    version = get_record(db, m.EvidenceVersion, file.evidence_version_id)
    visible = visible_tasks(db, user, 'team' if team_reader(db, user) else 'personal')
    permitted = db.scalar(select(m.EvidenceLink.id).where(
        m.EvidenceLink.evidence_id == version.evidence_id, m.EvidenceLink.task_id.in_(visible)).limit(1))
    if not permitted:
        raise HTTPException(403, 'No tienes acceso a la tarea de esta evidencia.')
    return file


@router.get('/evidence-files/{identifier}/preview')
def preview_file(identifier: str, user=Depends(current_user), db=Depends(get_db)):
    file = accessible_file(db, user, identifier)
    if Path(file.file_name).suffix.lower() not in {'.docx', '.xlsx', '.txt', '.csv'}:
        raise HTTPException(422, 'Este archivo se previsualiza directamente en el navegador.')
    return document_preview_bytes(read_object(file), file.file_name)


@router.get('/evidence-files/{identifier}')
def read_file(identifier: str, download: bool = False, user=Depends(current_user), db=Depends(get_db)):
    file = accessible_file(db, user, identifier)
    inline = not download and (file.content_type == 'application/pdf' or file.content_type.startswith('image/'))
    disposition = 'inline' if inline else 'attachment'
    return Response(read_object(file), media_type=file.content_type,
                        headers={'X-Content-Type-Options': 'nosniff', 'Cache-Control': 'no-store',
                                 'Content-Disposition': disposition + "; filename*=utf-8''" + quote(file.file_name, safe=''),
                                 'Content-Security-Policy': "default-src 'none'; sandbox"})
