"""Task membership, personal visibility and append-only progress validation."""
from fastapi import HTTPException
from sqlalchemy import select, or_, and_, func
from . import models as m
from .security import permissions


def supervises(db, user):
    return bool(permissions(db, user) & {'tasks.supervise', 'admin.write'})


def team_reader(db, user):
    return supervises(db, user) or 'tasks.team_read' in permissions(db, user)


def participant_ids(db, task):
    return {task.responsible_id} | set(db.scalars(select(m.TaskAssignment.user_id).where(m.TaskAssignment.task_id == task.id)))


def personal_condition(user, scope='personal'):
    assigned = select(m.TaskAssignment.task_id).where(m.TaskAssignment.user_id == user.id)
    delegated = select(m.TaskAssignment.task_id).where(m.TaskAssignment.assigned_by == user.id)
    involved = or_(m.Task.responsible_id == user.id, m.Task.id.in_(assigned))
    authored = or_(m.Task.created_by == user.id, m.Task.id.in_(delegated))
    if scope in {'received', 'mine'}:
        return involved
    if scope == 'assigned':
        return authored
    if scope == 'joint':
        count = select(func.count(m.TaskAssignment.id)).where(m.TaskAssignment.task_id == m.Task.id, m.TaskAssignment.user_id != m.Task.responsible_id).correlate(m.Task).scalar_subquery()
        return and_(involved, count > 0)
    return or_(involved, authored)


def visible_tasks(db, user, scope='personal'):
    stmt = select(m.Task.id)
    if scope == 'team':
        if not team_reader(db, user):
            raise HTTPException(403, 'La vista del equipo requiere jefatura o auditoría.')
        return stmt
    if scope not in {'personal', 'received', 'assigned', 'joint', 'mine'}:
        raise HTTPException(422, 'Vista de tareas no válida.')
    return stmt.where(personal_condition(user, scope))


def can_access(db, user, task):
    return team_reader(db, user) or db.scalar(select(m.Task.id).where(m.Task.id == task.id, personal_condition(user))) is not None


def require_access(db, user, task):
    if not can_access(db, user, task):
        raise HTTPException(403, 'Esta tarea no pertenece a tu espacio de trabajo.')


def require_participant(db, user, task):
    if user.id not in participant_ids(db, task):
        raise HTTPException(403, 'Solo los participantes registran su propio avance.')


def check_assignee(db, user_id):
    user = db.get(m.User, user_id)
    if not user or not user.active or 'tasks.write' not in permissions(db, user):
        raise HTTPException(422, 'Selecciona un integrante activo que pueda trabajar en tareas.')


def task_scope(db, name, stmt, user, scope='personal'):
    ids = visible_tasks(db, user, scope)
    model = {'tasks': m.Task, 'task-assignments': m.TaskAssignment, 'task-dependencies': m.TaskDependency,
             'task-updates': m.TaskUpdate, 'closure-approvals': m.ClosureApproval,
             'task-documents': m.TaskDocument}.get(name)
    if model:
        return stmt.where((model.id if name == 'tasks' else model.task_id).in_(ids))
    if name == 'task-update-reviews':
        return stmt.where(m.TaskUpdateReview.task_update_id.in_(select(m.TaskUpdate.id).where(m.TaskUpdate.task_id.in_(ids))))
    # Task evidence follows the same visibility rules, including versions and review history.
    linked = select(m.EvidenceLink.evidence_id).where(m.EvidenceLink.task_id.is_not(None))
    permitted = select(m.EvidenceLink.evidence_id).where(m.EvidenceLink.task_id.in_(ids))
    allowed = select(m.Evidence.id).where(or_(m.Evidence.id.not_in(linked), m.Evidence.id.in_(permitted), m.Evidence.author_id == user.id))
    if name == 'evidence':
        return stmt.where(m.Evidence.id.in_(allowed))
    if name in {'evidence-links', 'evidence-versions'}:
        model = m.EvidenceLink if name == 'evidence-links' else m.EvidenceVersion
        stmt = stmt.where(model.evidence_id.in_(allowed))
        if name == 'evidence-links':
            stmt = stmt.where(or_(model.task_id.is_(None), model.task_id.in_(ids)))
        return stmt
    if name == 'evidence-validations':
        return stmt.where(m.EvidenceValidation.evidence_version_id.in_(select(m.EvidenceVersion.id).where(m.EvidenceVersion.evidence_id.in_(allowed))))
    return stmt


def progress_summary(db, task):
    updates = list(db.scalars(select(m.TaskUpdate).where(m.TaskUpdate.task_id == task.id, m.TaskUpdate.kind == 'avance').order_by(m.TaskUpdate.created_at.desc(), m.TaskUpdate.id)))
    reviews = {r.task_update_id: r for r in db.scalars(select(m.TaskUpdateReview).where(m.TaskUpdateReview.task_update_id.in_([u.id for u in updates])))}
    people = []
    for identifier in sorted(participant_ids(db, task)):
        reports = [u for u in updates if u.author_id == identifier]
        latest = reports[0] if reports else None
        accepted = next((u for u in reports if u.id in reviews and reviews[u.id].status == 'validada'), None)
        person = db.get(m.User, identifier)
        review = reviews.get(latest.id) if latest else None
        people.append({'id': identifier, 'name': person.name if person else identifier,
                       'responsible': identifier == task.responsible_id,
                       'reported_progress': latest.progress if latest else 0,
                       'validated_progress': accepted.progress if accepted else 0,
                       'review_status': review.status if review else 'pendiente',
                       'latest_update_id': latest.id if latest else None})
    return {'participants': people,
            'reported_progress': round(sum(p['reported_progress'] for p in people) / len(people)) if people else 0,
            'validated_progress': round(sum(p['validated_progress'] for p in people) / len(people)) if people else 0,
            'all_complete': bool(people) and all(p['reported_progress'] == 100 and p['review_status'] == 'validada' for p in people)}


def sync_progress(db, task):
    db.flush()
    summary = progress_summary(db, task)
    task.progress = summary['validated_progress']
    task.status = 'en_revision' if all(p['reported_progress'] == 100 for p in summary['participants']) else 'en_progreso'
    return summary
