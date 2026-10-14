import calendar
import csv
import hashlib
import io
import secrets
from datetime import date, datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Request, Response, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, func, delete, update, inspect
from sqlalchemy.exc import IntegrityError
from . import models as m
from .db import get_db, engine
from .config import settings
from .security import current_user, permissions, roles, require, new_session, digest, hash_password, verify_password
from .task_policy import supervises, team_reader, task_scope, require_access, check_assignee, progress_summary, sync_progress
from .participant_routes import router as participant_router, enrollment_info
from .catalog import RESOURCES, READ_ONLY, LABELS, OPTIONS, STATUS_OPTIONS
from .service import resource, serialize, get_record, editable_columns, validate_data, check_business, check_ownership, filtered, enrich, audit
from .task_form import task_input, form_choices

app = FastAPI(title='ROADMAP OGC', version='0.1.0', docs_url='/api/docs', openapi_url='/api/openapi.json')
app.include_router(participant_router, prefix='/api')
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True,
                   allow_methods=['GET', 'POST', 'PATCH', 'OPTIONS'], allow_headers=['Content-Type', 'X-CSRF-Token'])


@app.middleware('http')
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.exception_handler(IntegrityError)
async def database_error(_, error):
    return JSONResponse(status_code=409, content={'detail': 'El registro está duplicado, tiene relaciones inexistentes o incumple una restricción.'})


@app.get('/api/health')
def health(db=Depends(get_db)):
    db.execute(select(1))
    return {'status': 'ok', 'environment': settings.app_env, 'demo': settings.demo_mode, 'database': engine.dialect.name}


class StrictInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class LoginInput(StrictInput):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


@app.post('/api/auth/login')
def login(body: LoginInput, request: Request, response: Response, db=Depends(get_db)):
    origin = request.headers.get('origin')
    if origin and origin not in settings.origins:
        raise HTTPException(403, 'Origen no autorizado.')
    key = digest((request.client.host if request.client else 'unknown') + ':' + body.email.lower())
    attempt = db.get(m.LoginAttempt, key)
    if attempt and attempt.window_start < m.now() - timedelta(minutes=15):
        attempt.failures, attempt.window_start = 0, m.now()
    if attempt and attempt.failures >= 8:
        raise HTTPException(429, 'Demasiados intentos. Espera 15 minutos.')
    user = db.scalar(select(m.User).where(m.User.email == body.email.lower()))
    # Always run a password derivation even for unknown accounts.
    valid = verify_password(body.password, user.password_hash) if user else verify_password(body.password, hash_password(secrets.token_urlsafe(32)))
    if not user or not user.active or not valid:
        if not attempt:
            attempt = m.LoginAttempt(id=key, failures=0)
            db.add(attempt)
        attempt.failures += 1
        db.commit()
        raise HTTPException(401, 'Correo o contraseña incorrectos.')
    if attempt:
        db.delete(attempt)
    old = request.cookies.get('ogc_session')
    if old:
        db.execute(delete(m.LoginSession).where(m.LoginSession.id == digest(old)))
    db.execute(delete(m.LoginSession).where(m.LoginSession.expires_at < m.now()))
    token, csrf = new_session(db, user)
    db.commit()
    response.set_cookie('ogc_session', token, httponly=True, secure=settings.cookie_secure,
                        samesite='none' if settings.cookie_secure else 'lax', max_age=settings.session_hours * 3600, path='/api')
    return {'user': serialize(user), 'roles': roles(db, user), 'permissions': sorted(permissions(db, user)), 'csrf_token': csrf, 'demo': settings.demo_mode, 'imports_enabled': settings.imports_enabled, **enrollment_info(db)}


@app.get('/api/auth/me')
def me(request: Request, user=Depends(current_user), db=Depends(get_db)):
    return {'user': serialize(user), 'roles': roles(db, user), 'permissions': sorted(permissions(db, user)),
            'csrf_token': digest(request.cookies['ogc_session'] + ':csrf'), 'demo': settings.demo_mode, 'imports_enabled': settings.imports_enabled, **enrollment_info(db)}


@app.post('/api/auth/logout')
def logout(request: Request, response: Response, user=Depends(current_user), db=Depends(get_db)):
    db.execute(delete(m.LoginSession).where(m.LoginSession.id == digest(request.cookies.get('ogc_session', ''))))
    db.commit()
    response.delete_cookie('ogc_session', path='/api', secure=settings.cookie_secure, samesite='none' if settings.cookie_secure else 'lax')
    return {'ok': True}


@app.get('/api/meta')
def metadata(user=Depends(current_user), db=Depends(get_db)):
    allowed = permissions(db, user)
    items = {}
    for name, (model, module, label) in RESOURCES.items():
        if module + '.read' not in allowed:
            continue
        fields = []
        for c in editable_columns(name):
            typ = c.type.python_type
            table = next(iter(c.foreign_keys)).column.table.name if c.foreign_keys else None
            lookup = next((key for key, spec in RESOURCES.items() if spec[0].__tablename__ == table), None)
            fields.append({'key': c.key, 'label': LABELS.get(c.key, c.key),
                           'type': {str: 'text', int: 'number', float: 'number', bool: 'boolean', date: 'date', datetime: 'datetime', dict: 'json'}.get(typ, 'text'),
                           'required': not c.nullable and not c.default, 'nullable': c.nullable, 'lookup': lookup,
                           'options': STATUS_OPTIONS.get(name, []) if c.key == 'status' else OPTIONS.get(c.key, []),
                           'default': c.default.arg if c.default and c.default.is_scalar else None})
        if name == 'users':
            fields.append({'key': 'password', 'label': 'Contraseña inicial / nueva', 'type': 'password', 'required': False})
        items[name] = {'label': label, 'module': module, 'fields': fields, 'readonly': name in READ_ONLY,
                       'can_write': module + '.write' in allowed and name not in READ_ONLY,
                       'can_validate': module + '.validate' in allowed}
    return items


@app.get('/api/lookups')
def lookups(user=Depends(current_user), db=Depends(get_db)):
    result = {}
    for name, (model, module, _) in RESOURCES.items():
        if module + '.read' not in permissions(db, user) or name in READ_ONLY:
            continue
        if name == 'users':
            stmt = select(model).where(model.active.is_(True))
        else:
            stmt = task_scope(db, name, select(model), user, 'team' if team_reader(db, user) else 'personal')
        records = db.scalars(stmt.order_by(model.created_at.desc()).limit(1000))
        result[name] = [{'value': r.id, 'label': getattr(r, 'title', getattr(r, 'name', getattr(r, 'number', r.id)))} for r in records]
        if name == 'projects':
            result[name] = [{'value': p.id, 'label': p.title, 'axis_id': p.axis_id} for p in db.scalars(select(m.Project).order_by(m.Project.created_at.desc()).limit(1000))]
        if name in {'evidence-versions', 'document-versions'}:
            parent_model = m.Evidence if name == 'evidence-versions' else m.Document
            parent_key = 'evidence_id' if name == 'evidence-versions' else 'document_id'
            versions = db.scalars(task_scope(db, name, select(model), user, 'team' if team_reader(db, user) else 'personal').order_by(model.created_at.desc()).limit(1000))
            result[name] = [{'value': v.id, 'label': f'{db.get(parent_model, getattr(v, parent_key)).title} · v{v.version}'} for v in versions]
    # User names are needed for operational selectors without administrative access.
    result['users'] = [{'value': r.id, 'label': r.name} for r in db.scalars(select(m.User).where(m.User.active.is_(True)).order_by(m.User.name))]
    result['task-members'] = [{'value': r.id, 'label': r.name} for r in db.scalars(select(m.User).where(m.User.active.is_(True)).order_by(m.User.name)) if 'tasks.write' in permissions(db, r)]
    result.update(form_choices(db))
    return result


@app.get('/api/dashboard')
def dashboard(request: Request, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'reports.read')
    params = dict(request.query_params)
    tasks = list(db.scalars(filtered(db, 'tasks', params, user)))
    projects = list(db.scalars(filtered(db, 'projects', params, user)))
    documents = list(db.scalars(filtered(db, 'documents', params, user)))
    agreements = list(db.scalars(filtered(db, 'agreements', params, user)))
    today = date.today()
    pending = [t for t in tasks if t.status != 'cerrada']
    overdue = [t for t in pending if t.due_date < today]
    upcoming = sorted([t for t in pending if today <= t.due_date <= today + timedelta(days=7)], key=lambda t: t.due_date)
    by_person = []
    summaries = {t.id: progress_summary(db, t) for t in tasks}
    for responsible in db.scalars(select(m.User).where(m.User.active.is_(True)).order_by(m.User.name)):
        assigned = [p for summary in summaries.values() for p in summary['participants'] if p['id'] == responsible.id]
        if assigned:
            by_person.append({'id': responsible.id, 'name': responsible.name, 'count': len(assigned),
                              'progress': round(sum(p['validated_progress'] for p in assigned) / len(assigned))})
    by_axis = []
    for axis in db.scalars(select(m.Axis).order_by(m.Axis.name)):
        ids = {p.id for p in projects if p.axis_id == axis.id}
        assigned = [t for t in tasks if t.project_id in ids]
        if assigned:
            by_axis.append({'id': axis.id, 'name': axis.name, 'color': axis.color, 'count': len(assigned), 'progress': round(sum(summaries[t.id]['validated_progress'] for t in assigned) / len(assigned))})
    return {'pending': len(pending), 'overdue': len(overdue), 'upcoming': len(upcoming),
            'pending_documents': sum(d.approval_status == 'pendiente' for d in documents),
            'pending_agreements': sum(a.status != 'cumplido' for a in agreements),
            'progress': round(sum(summaries[t.id]['validated_progress'] for t in tasks) / len(tasks)) if tasks else 0,
            'task_count': len(tasks), 'closed': sum(t.status == 'cerrada' for t in tasks),
            'by_person': by_person, 'by_axis': by_axis,
            'upcoming_tasks': [enrich(db, 'tasks', t, user) for t in upcoming[:8]],
            'overdue_tasks': [enrich(db, 'tasks', t, user) for t in sorted(overdue, key=lambda t: t.due_date)[:8]],
            'projects': [enrich(db, 'projects', p, user, params.get('scope', 'personal')) for p in projects[:6]],
            'recent_activity': [serialize(a) for a in db.scalars(select(m.Audit).where(m.Audit.actor_id == user.id, m.Audit.entity.not_in(['users', 'user-roles', 'role-permissions'])).order_by(m.Audit.created_at.desc()).limit(7))]}


@app.get('/api/alerts')
def alerts(request: Request, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'reports.read')
    result = []
    closed = {'cerrada', 'cumplido', 'conforme', 'aprobado', 'atendido', 'finalizada'}
    for name in ('tasks', 'agreements', 'deliverables', 'cases', 'evidence'):
        model, module, label = resource(name)
        require(db, user, module + '.read')
        stmt = filtered(db, name, dict(request.query_params), user).where(model.due_date <= date.today() + timedelta(days=7))
        for record in db.scalars(stmt):
            if getattr(record, 'status', '') in closed or (name == 'evidence' and record.request_status == 'recibida'):
                continue
            result.append({'entity': name, 'id': record.id, 'title': record.title, 'due_date': record.due_date,
                           'overdue': record.due_date < date.today(), 'label': label})
    return sorted(result, key=lambda a: a['due_date'])


@app.get('/api/reports/{name}.csv')
def report(name: str, request: Request, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'reports.read')
    model, module, _ = resource(name)
    require(db, user, module + '.read')
    if name in {'import-batches'}:
        raise HTTPException(403, 'Exportación no disponible para este recurso.')
    records = list(db.scalars(filtered(db, name, dict(request.query_params), user).order_by(model.created_at.desc()).limit(10001)))
    if len(records) > 10000:
        raise HTTPException(422, 'Reduce el rango del reporte a un máximo de 10 000 registros.')
    rows = [enrich(db, name, r, user) for r in records]
    fields = [c.key for c in model.__table__.columns if c.key != 'password_hash']
    if name == 'tasks':
        fields.extend(['participants', 'reported_progress', 'validated_progress'])
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([LABELS.get(key, key) for key in fields])
    for row in rows:
        values = []
        for key in fields:
            raw = ', '.join(p['name'] for p in row['participants']) if key == 'participants' else row['_labels'].get(key, row.get(key))
            value = str(raw) if raw is not None else ''
            # Prevent spreadsheet formula injection.
            values.append("'" + value if value.lstrip().startswith(('=', '+', '-', '@')) else value)
        writer.writerow(values)
    return Response('\ufeff' + output.getvalue(), media_type='text/csv; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="ogc-{name}-{date.today()}.csv"'})


def revision(record, expected):
    if record.revision != expected:
        raise HTTPException(409, 'Este registro cambió. Actualiza antes de guardar.')


def touch(db, user, name, record, action, before):
    record.modified_by = user.id
    record.revision += 1
    record.updated_at = m.now()
    audit(db, user, name, record, action, before)


from .task_routes import router as task_router
app.include_router(task_router, prefix='/api')


class CloseInput(StrictInput):
    revision: int
    evidence_version_id: str | None = None
    justification: str | None = Field(default=None, min_length=10, max_length=5000)


@app.post('/api/tasks/{identifier}/close')
def close_task(identifier: str, body: CloseInput, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'tasks.validate')
    if not supervises(db, user):
        raise HTTPException(403, 'El cierre corresponde al jefe.')
    task = get_record(db, m.Task, identifier, True)
    revision(task, body.revision)
    if task.status != 'en_revision' or task.progress != 100:
        raise HTTPException(422, 'La tarea debe estar en revisión y al 100 %.')
    if not progress_summary(db, task)['all_complete']:
        raise HTTPException(422, 'El jefe debe validar el último avance al 100 % de cada participante antes del cierre.')
    blockers = list(db.scalars(select(m.Task).join(m.TaskDependency, m.Task.id == m.TaskDependency.depends_on_id)
                             .where(m.TaskDependency.task_id == task.id, m.Task.status != 'cerrada')))
    children = list(db.scalars(select(m.Task).where(m.Task.parent_id == task.id, m.Task.status != 'cerrada')))
    if blockers or children:
        raise HTTPException(422, 'Cierra las dependencias y subtareas pendientes primero.')
    if body.evidence_version_id:
        version = get_record(db, m.EvidenceVersion, body.evidence_version_id, True)
        latest = db.scalar(select(func.max(m.EvidenceVersion.version)).where(m.EvidenceVersion.evidence_id == version.evidence_id))
        validation = db.scalar(select(m.EvidenceValidation).where(m.EvidenceValidation.evidence_version_id == version.id)
                               .order_by(m.EvidenceValidation.created_at.desc()).limit(1))
        link = db.scalar(select(m.EvidenceLink).where(m.EvidenceLink.evidence_id == version.evidence_id, m.EvidenceLink.task_id == task.id))
        if not link or version.version != latest or not validation or validation.status != 'validada' or not version.access_confirmed:
            raise HTTPException(422, 'El cierre requiere la última versión validada de una evidencia vinculada y con permisos confirmados.')
    elif not body.justification:
        raise HTTPException(422, 'Selecciona evidencia validada o registra una justificación autorizada.')
    before = serialize(task)
    task.status = 'cerrada'
    approval = m.ClosureApproval(task_id=task.id, approver_id=user.id, evidence_version_id=body.evidence_version_id, justification=body.justification, modified_by=user.id)
    db.add(approval)
    audit(db, user, 'closure-approvals', approval, 'create')
    for agreement in db.scalars(select(m.Agreement).where(m.Agreement.task_id == task.id)):
        prior = serialize(agreement)
        agreement.status = 'cumplido'
        touch(db, user, 'agreements', agreement, 'task_closed', prior)
    touch(db, user, 'tasks', task, 'close', before)
    # Generate the next occurrence once, within this transaction.
    if task.recurrence != 'ninguna':
        if task.recurrence == 'semanal':
            next_start, next_due = task.start_date + timedelta(days=7), task.due_date + timedelta(days=7)
        else:
            def next_month(value):
                month = value.month % 12 + 1
                year = value.year + (value.month == 12)
                return date(year, month, min(value.day, calendar.monthrange(year, month)[1]))
            next_start, next_due = next_month(task.start_date), next_month(task.due_date)
        recurring = m.Task(title=task.title, description=task.description, project_id=task.project_id, responsible_id=task.responsible_id,
                           office=task.office,
                           start_date=next_start, due_date=next_due, priority=task.priority, recurrence=task.recurrence,
                           recurrence_source_id=task.id, created_by=task.created_by or user.id, modified_by=user.id)
        db.add(recurring)
        audit(db, user, 'tasks', recurring, 'recurrence')
        for assignment in db.scalars(select(m.TaskAssignment).where(m.TaskAssignment.task_id == task.id)):
            db.add(m.TaskAssignment(task_id=recurring.id, user_id=assignment.user_id, assigned_by=user.id, modified_by=user.id))
    db.commit()
    return enrich(db, 'tasks', task, user)


class ValidationInput(StrictInput):
    status: str
    note: str = Field(min_length=3, max_length=5000)


@app.post('/api/evidence-versions/{identifier}/validate')
def validate_evidence(identifier: str, body: ValidationInput, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'evidence.validate')
    version = get_record(db, m.EvidenceVersion, identifier, True)
    linked_task = db.scalar(select(m.EvidenceLink.id).where(m.EvidenceLink.evidence_id == version.evidence_id, m.EvidenceLink.task_id.is_not(None)))
    if linked_task and not supervises(db, user):
        raise HTTPException(403, 'La evidencia de tareas debe ser revisada por el jefe.')
    if body.status not in {'validada', 'observada'} or (body.status == 'validada' and not version.access_confirmed):
        raise HTTPException(422, 'Confirma los permisos de acceso y el estado de validación.')
    item = m.EvidenceValidation(evidence_version_id=version.id, validator_id=user.id, status=body.status, note=body.note, modified_by=user.id)
    db.add(item)
    audit(db, user, 'evidence-validations', item, 'validate')
    db.commit()
    return serialize(item)


CASE_TRANSITIONS = {
    'elaboracion': {'revision'}, 'revision': {'firma', 'observado'}, 'firma': {'derivacion', 'observado'},
    'derivacion': {'aprobado', 'atendido', 'observado'}, 'observado': {'subsanacion'},
    'subsanacion': {'revision', 'derivacion'}, 'aprobado': set(), 'atendido': set(),
}


class StageInput(StrictInput):
    revision: int
    status: str
    department: str = Field(min_length=1, max_length=160)
    note: str = Field(min_length=3, max_length=5000)
    resolution_id: str | None = None


@app.post('/api/cases/{identifier}/stage')
def stage(identifier: str, body: StageInput, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'cases.write')
    case = get_record(db, m.Case, identifier, True)
    check_ownership(db, user, 'cases', case)
    revision(case, body.revision)
    if body.status not in CASE_TRANSITIONS.get(case.status, set()):
        raise HTTPException(422, 'La transición no corresponde a la etapa actual.')
    if body.status in {'aprobado', 'atendido'}:
        require(db, user, 'cases.validate')
        if not body.resolution_id:
            raise HTTPException(422, 'Selecciona el documento de resolución o atención.')
    before = serialize(case)
    case.status, case.current_department = body.status, body.department
    item = m.CaseEvent(case_id=case.id, actor_id=user.id, status=body.status, department=body.department, note=body.note, resolution_id=body.resolution_id, modified_by=user.id)
    db.add(item)
    audit(db, user, 'case-events', item, 'stage')
    touch(db, user, 'cases', case, 'stage', before)
    if body.status in {'aprobado', 'atendido'}:
        document = get_record(db, m.Document, case.document_id, True)
        prior = serialize(document)
        document.approval_status = body.status
        touch(db, user, 'documents', document, 'approval', prior)
    db.commit()
    return enrich(db, 'cases', case)


class RevisionInput(StrictInput):
    revision: int


@app.post('/api/agreements/{identifier}/task')
def task_from_agreement(identifier: str, body: RevisionInput, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'meetings.write')
    require(db, user, 'tasks.write')
    agreement = get_record(db, m.Agreement, identifier, True)
    check_ownership(db, user, 'agreements', agreement)
    if agreement.task_id:
        linked = get_record(db, m.Task, agreement.task_id)
        require_access(db, user, linked)
        return enrich(db, 'tasks', linked, user)
    revision(agreement, body.revision)
    before = serialize(agreement)
    task = m.Task(title=agreement.title, project_id=agreement.project_id, responsible_id=agreement.responsible_id,
                  start_date=min(date.today(), agreement.due_date), due_date=agreement.due_date,
                  description=f'Acuerdo de reunión {agreement.meeting_id}', created_by=user.id, modified_by=user.id)
    db.add(task)
    audit(db, user, 'tasks', task, 'from_agreement')
    agreement.task_id, agreement.status = task.id, 'en_progreso'
    touch(db, user, 'agreements', agreement, 'create_task', before)
    db.commit()
    return enrich(db, 'tasks', task, user)


class ReviewInput(ValidationInput):
    revision: int


@app.post('/api/deliverables/{identifier}/review')
def review_deliverable(identifier: str, body: ReviewInput, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'services.validate')
    item = get_record(db, m.Deliverable, identifier, True)
    revision(item, body.revision)
    if body.status not in {'en_revision', 'observado', 'conforme'}:
        raise HTTPException(422, 'Estado de revisión no válido.')
    if not item.presentation_document_id:
        raise HTTPException(422, 'Vincula el documento de presentación antes de revisar.')
    before = serialize(item)
    item.status = body.status
    review = m.DeliverableReview(deliverable_id=item.id, reviewer_id=user.id, status=body.status, note=body.note, modified_by=user.id)
    db.add(review)
    audit(db, user, 'deliverable-reviews', review, 'review')
    touch(db, user, 'deliverables', item, 'review', before)
    db.commit()
    return enrich(db, 'deliverables', item)


@app.post('/api/documents/{identifier}/send')
def send_document(identifier: str, body: RevisionInput, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'documents.write')
    document = get_record(db, m.Document, identifier, True)
    check_ownership(db, user, 'documents', document)
    revision(document, body.revision)
    if document.sent_date:
        raise HTTPException(409, 'Este documento ya fue remitido.')
    before = serialize(document)
    document.preparation_status, document.sent_date = 'remitido', date.today()
    touch(db, user, 'documents', document, 'send', before)
    db.commit()
    return enrich(db, 'documents', document)


@app.post('/api/quality-models/{identifier}/validate')
def validate_quality(identifier: str, body: RevisionInput, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'indicators.validate')
    item = get_record(db, m.QualityModel, identifier, True)
    revision(item, body.revision)
    if not item.source_url or not item.version:
        raise HTTPException(422, 'Registra la fuente y versión revisadas antes de activar el modelo.')
    prior = serialize(item)
    item.status, item.validated_by = 'validado', user.id
    touch(db, user, 'quality-models', item, 'validate', prior)
    db.commit()
    return serialize(item)


@app.post('/api/criteria/{identifier}/validate')
def validate_criterion(identifier: str, body: RevisionInput, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'indicators.validate')
    item = get_record(db, m.Criterion, identifier, True)
    revision(item, body.revision)
    model = get_record(db, m.QualityModel, item.quality_model_id)
    if model.status != 'validado':
        raise HTTPException(422, 'Valida el modelo y su versión antes de activar criterios.')
    prior = serialize(item)
    item.status = 'validado'
    touch(db, user, 'criteria', item, 'validate', prior)
    db.commit()
    return serialize(item)


@app.get('/api/{name}')
def list_records(name: str, request: Request, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), user=Depends(current_user), db=Depends(get_db)):
    model, module, _ = resource(name)
    require(db, user, module + '.read')
    stmt = filtered(db, name, dict(request.query_params), user)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    records = db.scalars(stmt.order_by(model.created_at.desc(), model.id).offset((page - 1) * page_size).limit(page_size))
    return {'items': [enrich(db, name, r, user) for r in records], 'total': total, 'page': page, 'page_size': page_size}


@app.get('/api/{name}/{identifier}')
def detail(name: str, identifier: str, user=Depends(current_user), db=Depends(get_db)):
    model, module, _ = resource(name)
    require(db, user, module + '.read')
    record = get_record(db, model, identifier)
    visible = db.scalar(task_scope(db, name, select(model), user, 'team' if team_reader(db, user) else 'personal').where(model.id == identifier))
    if visible is None:
        raise HTTPException(403, 'Este registro no pertenece a tu espacio de trabajo.')
    return enrich(db, name, record, user)


def writable(db, user, name):
    model, module, _ = resource(name)
    require(db, user, module + '.write')
    if name in READ_ONLY:
        raise HTTPException(403, 'Este registro solo se crea mediante su acción autorizada.')
    return model


def password_input(name, body, creating=False):
    data = dict(body)
    password = data.pop('password', None) if name == 'users' else None
    if name == 'users' and (creating or password):
        if not isinstance(password, str) or not 12 <= len(password) <= 256:
            raise HTTPException(422, 'La contraseña debe tener entre 12 y 256 caracteres.')
    return data, hash_password(password) if password else None


@app.post('/api/{name}', status_code=201)
def create_record(name: str, body: dict, user=Depends(current_user), db=Depends(get_db)):
    model = writable(db, user, name)
    raw, password = password_input(name, body, True)
    member_ids = raw.pop('member_ids', []) if name == 'tasks' else []
    if not isinstance(member_ids, list) or len(member_ids) > 1000 or any(not isinstance(v, str) for v in member_ids):
        raise HTTPException(422, 'Selecciona una lista de integrantes válida.')
    if name == 'tasks':raw = task_input(db,user,raw)
    data = validate_data(name, raw)
    if name == 'tasks':
        for identifier in set(member_ids):
            check_assignee(db, identifier)
        data['created_by'] = user.id
    if name == 'task-assignments':
        data['assigned_by'] = user.id
    check_ownership(db, user, name, data=data)
    check_business(db, name, data)
    if password:
        data['password_hash'] = password
    if name in {'document-versions', 'evidence-versions', 'evidence'}:
        data['author_id'] = user.id
    record = model(**data, modified_by=user.id)
    db.add(record)
    audit(db, user, name, record, 'create')
    if name == 'tasks':
        for identifier in set(member_ids) - {record.responsible_id}:
            assignment = m.TaskAssignment(task_id=record.id, user_id=identifier, assigned_by=user.id, modified_by=user.id)
            db.add(assignment)
            audit(db, user, 'task-assignments', assignment, 'create')
    if name == 'task-assignments':
        task = get_record(db, m.Task, record.task_id, True)
        before = serialize(task)
        sync_progress(db, task)
        touch(db, user, 'tasks', task, 'assign_participant', before)
    db.commit()
    return enrich(db, name, record, user)


@app.patch('/api/{name}/{identifier}')
def edit_record(name: str, identifier: str, body: dict, user=Depends(current_user), db=Depends(get_db)):
    model = writable(db, user, name)
    record = get_record(db, model, identifier, True)
    raw, password = password_input(name, body)
    expected = raw.pop('revision', None)
    if not isinstance(expected, int):
        raise HTTPException(422, 'La edición requiere la revisión actual del registro.')
    revision(record, expected)
    if name == 'tasks':raw = task_input(db,user,raw,record)
    data = validate_data(name, raw, True)
    check_ownership(db, user, name, record, data)
    check_business(db, name, data, record)
    if name == 'tasks' and 'responsible_id' in data and data['responsible_id'] != record.responsible_id:
        if db.scalar(select(m.TaskUpdate.id).where(m.TaskUpdate.task_id == record.id)):
            raise HTTPException(409, 'El responsable se conserva cuando ya existe un historial de avances.')
    if name == 'tasks' and record.status == 'cerrada':
        raise HTTPException(409, 'Las tareas cerradas no se editan.')
    if name in {'roles', 'role-permissions', 'user-roles'}:
        raise HTTPException(403, 'Las asignaciones y roles son inmutables. Usa las acciones de administración.')
    if name == 'users' and data.get('active') is False and record.id == user.id:
        raise HTTPException(422, 'No puedes desactivar tu propia sesión.')
    if name == 'quality-models' and any(key in data and data[key] != getattr(record, key) for key in ('version', 'source_url')):
        data['status'], data['validated_by'] = 'pendiente_validacion', None
        for criterion in db.scalars(select(m.Criterion).where(m.Criterion.quality_model_id == record.id)):
            prior = serialize(criterion)
            criterion.status = 'pendiente_validacion'
            touch(db, user, 'criteria', criterion, 'model_changed', prior)
    if name == 'criteria' and any(key in data and data[key] != getattr(record, key) for key in ('title', 'code', 'quality_model_id')):
        data['status'] = 'pendiente_validacion'
    before = serialize(record)
    if password:
        data['password_hash'] = password
    count = db.execute(update(model).where(model.id == identifier, model.revision == expected)
                       .values(**data, revision=expected + 1, modified_by=user.id, updated_at=m.now())).rowcount
    if count != 1:
        raise HTTPException(409, 'Edición simultánea. Actualiza el registro.')
    db.refresh(record)
    if name == 'users' and (password or data.get('active') is False):
        db.execute(delete(m.LoginSession).where(m.LoginSession.user_id == record.id))
    audit(db, user, name, record, 'update', before)
    db.commit()
    return enrich(db, name, record, user)


@app.post('/api/admin/{name}/{identifier}/revoke')
def revoke(name: str, identifier: str, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'admin.write')
    if name not in {'user-roles', 'role-permissions'}:
        raise HTTPException(404, 'Asignación no encontrada.')
    model, _, _ = resource(name)
    record = get_record(db, model, identifier, True)
    admin = db.scalar(select(m.Role).where(m.Role.name == 'administrador'))
    if record.role_id == admin.id:
        if name == 'role-permissions':
            raise HTTPException(422, 'No se pueden retirar permisos al rol de recuperación administrador.')
        if record.user_id == user.id:
            raise HTTPException(422, 'No puedes retirar tu propio rol administrador.')
    prior = serialize(record)
    db.add(m.Audit(actor_id=user.id, entity=name, record_id=record.id, action='revoke', before=prior, after=None))
    if name == 'user-roles':
        db.execute(delete(m.LoginSession).where(m.LoginSession.user_id == record.user_id))
    db.delete(record)
    db.commit()
    return {'ok': True}


# Import endpoints are registered before the generic POST path is matched by their depth.
from .importer import router as import_router
app.include_router(import_router, prefix='/api/import')
