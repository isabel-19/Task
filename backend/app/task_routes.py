from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, func
from . import models as m
from .db import get_db
from .security import current_user, require
from .service import get_record, serialize, audit, enrich, private_url
from .task_policy import require_access, require_participant, supervises, check_assignee, sync_progress

router = APIRouter()


class StrictInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class NewEvidence(StrictInput):
    title: str = Field(min_length=3, max_length=250)
    url: str = Field(min_length=1, max_length=4000)
    access_confirmed: bool = False


class AdvanceInput(StrictInput):
    revision: int
    progress: int = Field(ge=0, le=100)
    comment: str = Field(min_length=1, max_length=5000)
    kind: str = 'avance'
    request_review: bool = False
    evidence_version_id: str | None = None
    evidence: NewEvidence | None = None


def touch(db, user, task, before, action):
    task.revision += 1
    task.modified_by = user.id
    task.updated_at = m.now()
    audit(db, user, 'tasks', task, action, before)


def expected_revision(task, expected):
    if task.revision != expected:
        raise HTTPException(409, 'La tarea cambió. Actualiza antes de guardar.')
    if task.status == 'cerrada':
        raise HTTPException(409, 'La tarea ya está cerrada.')


@router.post('/tasks/{identifier}/advance')
def advance(identifier: str, body: AdvanceInput, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'tasks.write')
    task = get_record(db, m.Task, identifier, True)
    require_participant(db, user, task)
    expected_revision(task, body.revision)
    if body.kind not in {'avance', 'comentario', 'observacion'}:
        raise HTTPException(422, 'Tipo de actuación no válido.')
    if body.request_review and (body.progress != 100 or body.kind != 'avance'):
        raise HTTPException(422, 'Completa tu avance al 100 % para solicitar cierre.')
    if body.evidence and body.evidence_version_id:
        raise HTTPException(422, 'Adjunta una evidencia nueva o una versión existente.')
    version_id = body.evidence_version_id
    if body.kind == 'avance':
        require(db, user, 'evidence.write')
        if body.evidence:
            private_url(body.evidence.url)
            if not body.evidence.access_confirmed:
                raise HTTPException(422, 'Confirma que el jefe puede acceder a la evidencia.')
            evidence = m.Evidence(title=body.evidence.title, category='Avance de tarea', date=date.today(), author_id=user.id, modified_by=user.id)
            db.add(evidence)
            audit(db, user, 'evidence', evidence, 'create')
            version = m.EvidenceVersion(evidence_id=evidence.id, version=1, url=body.evidence.url, access_confirmed=True, author_id=user.id, modified_by=user.id)
            db.add(version)
            audit(db, user, 'evidence-versions', version, 'create')
            link = m.EvidenceLink(evidence_id=evidence.id, task_id=task.id, modified_by=user.id)
            db.add(link)
            audit(db, user, 'evidence-links', link, 'create')
            version_id = version.id
        elif version_id:
            version = get_record(db, m.EvidenceVersion, version_id, True)
            link = db.scalar(select(m.EvidenceLink.id).where(m.EvidenceLink.task_id == task.id, m.EvidenceLink.evidence_id == version.evidence_id))
            latest = db.scalar(select(func.max(m.EvidenceVersion.version)).where(m.EvidenceVersion.evidence_id == version.evidence_id))
            if not link or version.author_id != user.id or not version.access_confirmed or version.version != latest:
                raise HTTPException(422, 'Selecciona tu última versión de evidencia vinculada a la tarea, con acceso confirmado.')
        else:
            raise HTTPException(422, 'Adjunta una evidencia para registrar tu avance.')
    elif body.evidence or version_id:
        raise HTTPException(422, 'Adjunta evidencias mediante un registro de avance.')
    before = serialize(task)
    item = m.TaskUpdate(task_id=task.id, author_id=user.id, progress=body.progress, comment=body.comment, kind=body.kind, evidence_version_id=version_id, modified_by=user.id)
    db.add(item)
    audit(db, user, 'task-updates', item, 'create')
    if body.kind == 'avance':
        sync_progress(db, task)
    touch(db, user, task, before, body.kind)
    db.commit()
    return enrich(db, 'tasks', task, user)


class ParticipantsInput(StrictInput):
    revision: int
    member_ids: list[str] = Field(min_length=1, max_length=1000)


@router.post('/tasks/{identifier}/participants')
def add_participants(identifier: str, body: ParticipantsInput, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'tasks.write')
    task = get_record(db, m.Task, identifier, True)
    require_access(db, user, task)
    expected_revision(task, body.revision)
    # Any current participant or assigning user can invite colleagues.
    current = enrich(db, 'tasks', task, user)
    if not current['can_assign']:
        raise HTTPException(403, 'Solo el equipo de la tarea puede agregar integrantes.')
    for identifier in set(body.member_ids):
        check_assignee(db, identifier)
    before = serialize(task)
    added = False
    for identifier in set(body.member_ids) - set(current['member_ids']):
        item = m.TaskAssignment(task_id=task.id, user_id=identifier, assigned_by=user.id, modified_by=user.id)
        db.add(item)
        audit(db, user, 'task-assignments', item, 'create')
        added = True
    if added:
        sync_progress(db, task)
        touch(db, user, task, before, 'assign_participants')
    db.commit()
    return enrich(db, 'tasks', task, user)


class ReviewInput(StrictInput):
    revision: int
    status: str
    note: str = Field(min_length=3, max_length=5000)


@router.post('/task-updates/{identifier}/review')
def review_update(identifier: str, body: ReviewInput, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'tasks.validate')
    if not supervises(db, user):
        raise HTTPException(403, 'La validación de avances corresponde al jefe.')
    item = get_record(db, m.TaskUpdate, identifier)
    task = get_record(db, m.Task, item.task_id, True)
    expected_revision(task, body.revision)
    if body.status not in {'validada', 'observada'}:
        raise HTTPException(422, 'Selecciona validada u observada.')
    if not enrich(db, 'task-updates', item, user)['can_review']:
        raise HTTPException(409, 'Este avance ya fue revisado, es anterior al último envío o no tiene evidencia.')
    version = get_record(db, m.EvidenceVersion, item.evidence_version_id, True)
    if body.status == 'validada' and not version.access_confirmed:
        raise HTTPException(422, 'Confirma el acceso a la evidencia antes de validar.')
    before = serialize(task)
    review = m.TaskUpdateReview(task_update_id=item.id, reviewer_id=user.id, status=body.status, note=body.note, modified_by=user.id)
    db.add(review)
    audit(db, user, 'task-update-reviews', review, 'review')
    validation = m.EvidenceValidation(evidence_version_id=version.id, validator_id=user.id, status=body.status, note=body.note, modified_by=user.id)
    db.add(validation)
    audit(db, user, 'evidence-validations', validation, 'validate')
    sync_progress(db, task)
    touch(db, user, task, before, 'review_progress')
    db.commit()
    return enrich(db, 'tasks', task, user)
