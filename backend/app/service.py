"""Shared validation, transaction audit and filtering for explicit relational resources."""
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlparse
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import ConfigDict, Field, ValidationError, create_model
from sqlalchemy import select, or_, func
from sqlalchemy.inspection import inspect
from . import models as m
from .catalog import RESOURCES, SYSTEM_FIELDS, CONTROLLED, OPTIONS, STATUS_OPTIONS
from .security import permissions
from .validation import validation_details
from .task_policy import task_scope, supervises, team_reader, can_access, require_access, check_assignee, progress_summary, pending_reviews_statement
from .evidence_storage import file_metadata


def resource(name):
    if name not in RESOURCES:
        raise HTTPException(404, 'Recurso no encontrado.')
    return RESOURCES[name]


def serialize(record):
    values = {}
    for column in inspect(record).mapper.columns:
        if column.key == 'password_hash':
            continue
        value = getattr(record, column.key)
        # Stored audit instants are UTC; meeting dates remain office calendar times.
        if column.key.endswith('_at') and isinstance(value, datetime):
            value = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
        values[column.key] = value
    return jsonable_encoder(values)


def audit(db, user, name, record, action, before=None):
    db.flush()
    db.add(m.Audit(actor_id=user.id, entity=name, record_id=record.id, action=action,
                   before=before, after=serialize(record)))


def get_record(db, model, identifier, lock=False):
    statement = select(model).where(model.id == identifier)
    if lock:
        statement = statement.with_for_update()
    record = db.scalar(statement)
    if record is None:
        raise HTTPException(404, 'Registro no encontrado.')
    return record


def private_url(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname not in {'drive.google.com', 'docs.google.com'} or p.username or p.password:
        raise HTTPException(422, 'Usa un enlace HTTPS de Google Drive/Docs institucional. Confirma sus permisos de acceso.')
    return url


def document_url(url):
    p = urlparse(url)
    host = (p.hostname or '').lower()
    if p.scheme != 'https' or p.username or p.password or not (
        host in {'drive.google.com', 'docs.google.com', 'unajma.edu.pe'} or host.endswith('.unajma.edu.pe')
    ):
        raise HTTPException(422, 'Pega un enlace HTTPS de Google Drive, Google Docs o del sitio institucional de UNAJMA.')
    return url


def editable_columns(name):
    model, _, _ = resource(name)
    return [c for c in model.__table__.columns if c.key not in SYSTEM_FIELDS | CONTROLLED.get(name, set())]


def validate_data(name, body, partial=False):
    fields = {}
    for c in editable_columns(name):
        pytype = c.type.python_type
        default = None if c.nullable or partial else (c.default.arg if c.default and c.default.is_scalar else ...)
        annotation = pytype | None if c.nullable else pytype
        kwargs = {}
        if pytype is str:
            kwargs = {'min_length': 1}
            if getattr(c.type, 'length', None):
                kwargs['max_length'] = c.type.length
        if c.key in {'version', 'year'} and pytype is int:
            kwargs['ge'] = 1
        if c.key in {'target', 'result'}:
            kwargs['ge'] = 0
        fields[c.key] = (annotation, Field(default=default, **kwargs))
    schema = create_model(f'{name}Input', __config__=ConfigDict(extra='forbid', str_strip_whitespace=True), **fields)
    try:
        data = schema.model_validate(body).model_dump(exclude_unset=partial)
    except ValidationError as error:
        raise HTTPException(422, validation_details(error.errors())) from error
    for key, value in data.items():
        choices = STATUS_OPTIONS.get(name) if key == 'status' else OPTIONS.get(key)
        if choices and value is not None and value not in choices:
            raise HTTPException(422, f'Valor no válido para {key}.')
    if data.get('url'):
        (document_url if name == 'document-versions' else private_url)(data['url'])
    if data.get('email_url'):
        p = urlparse(data['email_url'])
        if p.scheme != 'https' or not p.hostname or p.username or p.password:
            raise HTTPException(422, 'Usa un enlace HTTPS válido para el correo.')
    if data.get('email'):
        data['email'] = data['email'].lower()
        if '@' not in data['email'] or '.' not in data['email'].split('@')[-1]:
            raise HTTPException(422, 'Correo no válido.')
    return data


def check_business(db, name, data, existing=None):
    if name == 'documents':
        from .document_workflow import validate_workflow
        validate_workflow(db, data, existing)
    merged = (serialize(existing) if existing else {}) | data
    if merged.get('start_date') and merged.get('due_date') and str(merged['due_date']) < str(merged['start_date']):
        raise HTTPException(422, 'El plazo no puede ser anterior al inicio.')
    if name == 'task-dependencies':
        source, target = merged['task_id'], merged['depends_on_id']
        edges = list(db.execute(select(m.TaskDependency.task_id, m.TaskDependency.depends_on_id)))
        graph = {}
        for a, b in edges:
            graph.setdefault(a, []).append(b)
        visited, stack = set(), [target]
        while stack:
            current = stack.pop()
            if current == source:
                raise HTTPException(422, 'La dependencia generaría un ciclo.')
            if current not in visited:
                visited.add(current)
                stack.extend(graph.get(current, []))
    if name == 'tasks' and merged.get('parent_id'):
        parent = get_record(db, m.Task, merged['parent_id'])
        if parent.project_id != merged.get('project_id'):
            raise HTTPException(422, 'La subtarea debe pertenecer al mismo proyecto.')
        visited = {existing.id} if existing else set()
        while parent:
            if parent.id in visited:
                raise HTTPException(422, 'Jerarquía circular de subtareas.')
            visited.add(parent.id)
            parent = db.get(m.Task, parent.parent_id) if parent.parent_id else None
    if name in {'evidence-versions', 'document-versions'} and existing:
        raise HTTPException(409, 'Las versiones son inmutables; registra una nueva versión.')
    if name == 'evidence-links':
        targets = [key for key in ('task_id', 'document_id', 'agreement_id', 'meeting_id', 'project_id', 'indicator_id') if merged.get(key)]
        if len(targets) != 1:
            raise HTTPException(422, 'Selecciona exactamente un destino para la evidencia.')
    if name == 'indicator-results':
        indicator = get_record(db, m.Indicator, merged['indicator_id'])
        if indicator.unit == '%' and (merged.get('target', 0) > 100 or merged.get('result', 0) > 100):
            raise HTTPException(422, 'Los porcentajes deben estar entre 0 y 100.')


def owns_task(db, user, task_id):
    task = get_record(db, m.Task, task_id)
    return task.responsible_id == user.id or db.scalar(select(m.TaskAssignment.id).where(m.TaskAssignment.task_id == task.id, m.TaskAssignment.user_id == user.id)) is not None


def check_ownership(db, user, name, existing=None, data=None):
    _, module, _ = resource(name)
    data = data or {}
    if existing and name != 'tasks':
        model = type(existing)
        visible = db.scalar(task_scope(db, name, select(model), user, 'team' if team_reader(db, user) else 'personal').where(model.id == existing.id))
        if visible is None:
            raise HTTPException(403, 'Este registro no pertenece a tu espacio de trabajo.')
    for field, related_name, model in [('evidence_id', 'evidence', m.Evidence), ('evidence_version_id', 'evidence-versions', m.EvidenceVersion)]:
        if data.get(field):
            parent = get_record(db, model, data[field])
            visible = db.scalar(task_scope(db, related_name, select(model), user, 'team' if team_reader(db, user) else 'personal').where(model.id == parent.id))
            if visible is None:
                raise HTTPException(403, 'La evidencia no pertenece a tu espacio de trabajo.')
    if name == 'tasks':
        if existing:
            require_access(db, user, existing)
            if not supervises(db, user) and existing.created_by != user.id:
                raise HTTPException(403, 'La edición de la tarea corresponde a quien la asignó o al jefe.')
        if data.get('responsible_id'):
            check_assignee(db, data['responsible_id'])
        for key in ('parent_id', 'recurrence_source_id'):
            if data.get(key):
                require_access(db, user, get_record(db, m.Task, data[key]))
        return
    task_id = data.get('task_id') or (getattr(existing, 'task_id', None) if existing else None)
    if task_id:
        task = get_record(db, m.Task, task_id)
        require_access(db, user, task)
        if not supervises(db, user) and task.created_by != user.id and not owns_task(db, user, task_id):
            raise HTTPException(403, 'Solo el equipo de la tarea puede agregar vínculos o integrantes.')
        if existing and data.get('task_id') and data['task_id'] != existing.task_id:
            raise HTTPException(422, 'No se puede trasladar este vínculo a otra tarea.')
        if name == 'task-assignments':
            if existing:
                raise HTTPException(403, 'Las asignaciones conservan su autor; agrega otra asignación.')
            check_assignee(db, data['user_id'])
        if name == 'task-dependencies' and data.get('depends_on_id'):
            require_access(db, user, get_record(db, m.Task, data['depends_on_id']))
        if task.status == 'cerrada':
            raise HTTPException(409, 'La tarea ya está cerrada.')
        return
    if f'{module}.validate' in permissions(db, user) or 'admin.write' in permissions(db, user):
        return
    data = data or {}
    if existing and hasattr(existing, 'responsible_id'):
        permitted = owns_task(db, user, existing.id) if name == 'tasks' else existing.responsible_id == user.id
        if not permitted:
            raise HTTPException(403, 'Solo puedes modificar registros a tu cargo.')
    if 'responsible_id' in data and data['responsible_id'] != user.id:
        raise HTTPException(403, 'Solo coordinación puede asignar a otro responsable.')
    if existing and hasattr(existing, 'author_id') and existing.author_id != user.id:
        raise HTTPException(403, 'Solo puedes modificar tus propios registros.')
    task_id = data.get('task_id') or (getattr(existing, 'task_id', None) if existing else None)
    if task_id and not owns_task(db, user, task_id):
        raise HTTPException(403, 'La tarea no está asignada a tu usuario.')
    # Reference tables/catalogs are managed by coordinators, not by members.
    if name in {'axes', 'processes', 'milestones', 'document-types', 'quality-models', 'criteria', 'periods', 'task-assignments', 'task-dependencies'}:
        raise HTTPException(403, 'Esta configuración requiere coordinación.')
    for field, model in [('meeting_id', m.Meeting), ('document_id', m.Document), ('project_id', m.Project), ('service_order_id', m.ServiceOrder), ('indicator_id', m.Indicator), ('evidence_id', m.Evidence)]:
        value = data.get(field)
        if value and not task_id:
            parent = get_record(db, model, value)
            owner = getattr(parent, 'responsible_id', getattr(parent, 'author_id', None))
            if owner != user.id:
                raise HTTPException(403, 'El registro relacionado no está a tu cargo.')


def filtered(db, name, params, user=None):
    model, _, _ = resource(name)
    stmt = select(model)
    if user:
        stmt = task_scope(db, name, stmt, user, params.get('scope', 'personal'))
    if name == 'tasks' and params.get('pending_review') == 'true':
        if not user or not supervises(db, user) or 'tasks.validate' not in permissions(db, user):
            raise HTTPException(403, 'Las evidencias pendientes de revisión corresponden a jefatura.')
        stmt = stmt.where(m.Task.id.in_(pending_reviews_statement(user.id).with_only_columns(m.TaskUpdate.task_id)))
    q = params.get('q', '').strip()
    if q:
        matches = [getattr(model, c.key).icontains(q, autoescape=True)
                   for c in model.__table__.columns
                   if c.type.python_type is str and c.key not in SYSTEM_FIELDS and not c.foreign_keys]
        for column in model.__table__.columns:
            if not column.foreign_keys or column.key in SYSTEM_FIELDS:
                continue
            table = next(iter(column.foreign_keys)).column.table.name
            target = next(((key, spec[0]) for key, spec in RESOURCES.items() if spec[0].__tablename__ == table), None)
            if not target:
                continue
            target_name, target_model = target
            labels = [getattr(target_model, key).icontains(q, autoescape=True)
                      for key in ('title', 'name', 'number') if hasattr(target_model, key)]
            if labels:
                linked = select(target_model.id).where(or_(*labels))
                if user:
                    linked = task_scope(db, target_name, linked, user, params.get('scope', 'personal'))
                matches.append(getattr(model, column.key).in_(linked))
        # Never silently ignore a visible search control on a relational resource.
        if name == 'tasks':
            people = select(m.User.id).where(m.User.name.icontains(q, autoescape=True))
            matches.append(m.Task.id.in_(select(m.TaskAssignment.task_id).where(m.TaskAssignment.user_id.in_(people))))
        stmt = stmt.where(or_(*matches) if matches else False)
    for c in model.__table__.columns:
        if c.key in SYSTEM_FIELDS | {'password_hash'}:
            continue
        if c.key in params and params[c.key] != '':
            try:
                typ = c.type.python_type
                raw = params[c.key]
                val = date.fromisoformat(raw) if typ is date else (raw.lower() == 'true' if typ is bool else typ(raw))
                if name == 'tasks' and c.key == 'responsible_id':
                    stmt = stmt.where(or_(m.Task.responsible_id == val, m.Task.id.in_(select(m.TaskAssignment.task_id).where(m.TaskAssignment.user_id == val))))
                else:
                    stmt = stmt.where(getattr(model, c.key) == val)
            except (ValueError, TypeError):
                raise HTTPException(422, f'Filtro no válido: {c.key}.')
    if params.get('axis_id') or params.get('process_id'):
        if hasattr(model, 'project_id'):
            projects = select(m.Project.id)
            inherited_filter = False
            for key in ('axis_id', 'process_id'):
                if params.get(key) and not hasattr(model, key):
                    projects = projects.where(getattr(m.Project, key) == params[key])
                    inherited_filter = True
            if inherited_filter:
                stmt = stmt.where(model.project_id.in_(projects))
    date_field = next((getattr(model, k) for k in ('due_date', 'date', 'start_date') if hasattr(model, k)), model.created_at)
    for key in ('year', 'month'):
        if params.get(key) and not (key == 'year' and hasattr(model, 'year')):
            try:
                val = int(params[key])
            except ValueError:
                raise HTTPException(422, 'Periodo no válido.')
            if key == 'month' and not 1 <= val <= 12:
                raise HTTPException(422, 'Mes no válido.')
            stmt = stmt.where(func.extract(key, date_field) == val)
    lower = upper = None
    if params.get('from'):
        try:
            lower = date.fromisoformat(params['from'])
            stmt = stmt.where(date_field >= lower)
        except ValueError:
            raise HTTPException(422, 'Fecha inicial no válida.')
    if params.get('to'):
        try:
            upper = date.fromisoformat(params['to'])
            if date_field.type.python_type is datetime:
                stmt = stmt.where(date_field < datetime.combine(upper + timedelta(days=1), datetime.min.time()))
            else:
                stmt = stmt.where(date_field <= upper)
        except ValueError:
            raise HTTPException(422, 'Fecha final no válida.')
    if lower and upper and lower > upper:
        raise HTTPException(422, 'La fecha inicial no puede ser posterior a la fecha final.')
    if params.get('overdue') == 'true' and hasattr(model, 'due_date'):
        stmt = stmt.where(model.due_date < date.today())
        if hasattr(model, 'status'):
            stmt = stmt.where(model.status.not_in(['cerrada', 'cumplido', 'cumplida', 'conforme', 'aprobado', 'atendido', 'finalizado', 'finalizada']))
    if params.get('mine') == 'true' and user:
        if name == 'tasks':
            assigned = select(m.TaskAssignment.task_id).where(m.TaskAssignment.user_id == user.id)
            stmt = stmt.where(or_(m.Task.responsible_id == user.id, m.Task.id.in_(assigned)))
        elif hasattr(model, 'responsible_id'):
            stmt = stmt.where(model.responsible_id == user.id)
    return stmt


def enrich(db, name, record, user=None, scope='personal'):
    result = serialize(record)
    labels = {}
    for c in record.__table__.columns:
        if c.foreign_keys and getattr(record, c.key, None):
            table = next(iter(c.foreign_keys)).column.table.name
            match = next((spec[0] for spec in RESOURCES.values() if spec[0].__tablename__ == table), None)
            linked = db.get(match, getattr(record, c.key)) if match else None
            if linked:
                labels[c.key] = 'Tarea fuera de tu espacio' if user and isinstance(linked, m.Task) and not can_access(db, user, linked) else getattr(linked, 'title', getattr(linked, 'name', getattr(linked, 'number', linked.id)))
    result['_labels'] = labels
    if name == 'documents':
        from .document_workflow import display_status
        result['document_status'] = display_status(record)
        completed = record.attended or (record.section == 'recibidos' and record.approval_status in ['aprobado', 'atendido'])
        result['days_remaining'] = (record.due_date - date.today()).days if record.due_date else None
        result['deadline_status'] = 'completo' if completed else 'sin_plazo' if not record.due_date else 'vencido' if record.due_date < date.today() else 'en_plazo'
        version = db.scalar(select(m.DocumentVersion).where(m.DocumentVersion.document_id == record.id)
                            .order_by(m.DocumentVersion.version.desc()).limit(1))
        result['url'] = version.url if version else None
        result['version'] = version.version if version else 0
        result['access_confirmed'] = version.access_confirmed if version else False
    if name == 'tasks':
        project=db.get(m.Project,record.project_id)
        axis=db.get(m.Axis,project.axis_id) if project else None
        result['axis_id']=axis.id if axis else None
        result['theme']=axis.name if axis else None
        result.update(progress_summary(db, record))
        reports = list(db.scalars(select(m.TaskUpdate).where(
            m.TaskUpdate.task_id == record.id, m.TaskUpdate.kind == 'avance',
            m.TaskUpdate.evidence_version_id.is_not(None),
        ).order_by(m.TaskUpdate.created_at.desc(), m.TaskUpdate.id)))
        result['evidence_count'] = len(reports)
        latest_version = db.get(m.EvidenceVersion, reports[0].evidence_version_id) if reports else None
        result['latest_evidence_url'] = latest_version.url if latest_version else None
        latest_file = db.scalar(select(m.EvidenceFile).where(m.EvidenceFile.evidence_version_id == latest_version.id)) if latest_version else None
        result['latest_evidence_file'] = file_metadata(latest_file) if latest_file else None
        # Keep files linked before the simplified contribution flow accessible.
        reported_evidence = select(m.EvidenceVersion.evidence_id).where(
            m.EvidenceVersion.id.in_([item.evidence_version_id for item in reports]))
        attachments = []
        for evidence in db.scalars(select(m.Evidence).join(m.EvidenceLink, m.EvidenceLink.evidence_id == m.Evidence.id).where(
                m.EvidenceLink.task_id == record.id, m.Evidence.id.not_in(reported_evidence)).order_by(m.Evidence.created_at.desc(), m.Evidence.id)):
            version = db.scalar(select(m.EvidenceVersion).where(m.EvidenceVersion.evidence_id == evidence.id).order_by(m.EvidenceVersion.version.desc()).limit(1))
            file = db.scalar(select(m.EvidenceFile).where(m.EvidenceFile.evidence_version_id == version.id)) if version else None
            attachments.append({'id': evidence.id, 'title': evidence.title, 'kind': 'evidence', 'url': version.url if version else None, 'file': file_metadata(file) if file else None})
        result['evidence_count'] += len(attachments)
        for document in db.scalars(select(m.Document).join(m.TaskDocument, m.TaskDocument.document_id == m.Document.id).where(
                m.TaskDocument.task_id == record.id).order_by(m.Document.created_at.desc(), m.Document.id)):
            version = db.scalar(select(m.DocumentVersion).where(m.DocumentVersion.document_id == document.id).order_by(m.DocumentVersion.version.desc()).limit(1))
            attachments.append({'id': document.id, 'title': document.title, 'kind': 'document', 'url': version.url if version else None})
        result['document_count'] = sum(item['kind'] == 'document' for item in attachments)
        result['attachments'] = attachments
        if not result['latest_evidence_url']:
            result['latest_evidence_url'] = next((item['url'] for item in attachments if item['url']), None)
            result['latest_evidence_file'] = next((item['file'] for item in attachments if item.get('file') and item['url'] == result['latest_evidence_url']), None)
        result['progress'] = result['validated_progress']
        if record.progress != result['validated_progress']:
            result['legacy_progress'] = record.progress
        result['member_ids'] = [p['id'] for p in result['participants']]
        if user:
            result['can_edit'] = record.status != 'cerrada' and (supervises(db, user) or record.created_by == user.id)
            result['can_advance'] = record.status != 'cerrada' and user.id in result['member_ids'] and 'tasks.write' in permissions(db, user)
            result['can_assign'] = record.status != 'cerrada' and 'tasks.write' in permissions(db, user) and (supervises(db, user) or record.created_by == user.id or user.id in result['member_ids'])
            result['can_review'] = supervises(db, user) and 'tasks.validate' in permissions(db, user)
    if name == 'task-updates':
        review = db.scalar(select(m.TaskUpdateReview).where(m.TaskUpdateReview.task_update_id == record.id))
        result['review_status'] = review.status if review else 'pendiente'
        result['review_note'] = review.note if review else None
        result['reviewer'] = db.get(m.User, review.reviewer_id).name if review else None
        version = db.get(m.EvidenceVersion, record.evidence_version_id) if record.evidence_version_id else None
        result['url'] = version.url if version else None
        file = db.scalar(select(m.EvidenceFile).where(m.EvidenceFile.evidence_version_id == version.id)) if version else None
        result['file'] = file_metadata(file) if file else None
        latest = db.scalar(select(m.TaskUpdate.id).where(m.TaskUpdate.task_id == record.task_id, m.TaskUpdate.author_id == record.author_id, m.TaskUpdate.kind == 'avance').order_by(m.TaskUpdate.created_at.desc(), m.TaskUpdate.id).limit(1))
        result['superseded'] = record.kind == 'avance' and not review and latest != record.id
        task = db.get(m.Task, record.task_id)
        result['can_review'] = bool(user and user.id != record.author_id and supervises(db, user) and 'tasks.validate' in permissions(db, user) and record.kind == 'avance' and record.evidence_version_id and not review and latest == record.id and task.status != 'cerrada')
    if name == 'projects':
        stmt = select(m.Task).where(m.Task.project_id == record.id)
        if user:
            stmt = task_scope(db, 'tasks', stmt, user, scope)
        tasks = list(db.scalars(stmt))
        result['progress'] = round(sum(progress_summary(db, t)['validated_progress'] for t in tasks) / len(tasks)) if tasks else 0
        result['task_count'] = len(tasks)
    if name == 'evidence':
        version = db.scalar(select(m.EvidenceVersion).where(m.EvidenceVersion.evidence_id == record.id).order_by(m.EvidenceVersion.version.desc()).limit(1))
        validation = db.scalar(select(m.EvidenceValidation).where(m.EvidenceValidation.evidence_version_id == version.id).order_by(m.EvidenceValidation.created_at.desc()).limit(1)) if version else None
        result['validation_status'] = validation.status if validation else 'pendiente'
        result['version'] = version.version if version else 0
        result['url'] = version.url if version else None
    return result
