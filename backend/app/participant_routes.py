from fastapi import APIRouter, Depends
from sqlalchemy import select
from . import models as m
from .db import get_db
from .security import current_user, require, roles, permissions
from .participant_import import imported_people, person_key
from .task_policy import team_reader, visible_tasks

router = APIRouter()


def enrollment_info(db):
    count = len(imported_people(db))
    return {'imported_participants': count, 'has_real_participants': count > 0}


@router.get('/participants')
def participants(user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'tasks.read')
    imported = imported_people(db)
    task_ids = visible_tasks(db, user, 'team' if team_reader(db, user) else 'personal')
    responsibilities = list(db.execute(select(m.Task.id, m.Task.responsible_id).where(m.Task.id.in_(task_ids))))
    assignments = list(db.execute(select(m.TaskAssignment.task_id, m.TaskAssignment.user_id).where(m.TaskAssignment.task_id.in_(task_ids))))
    users = list(db.scalars(select(m.User).where(m.User.active.is_(True)).order_by(m.User.name)))
    names = {person_key(person.name): person.name for person in users}
    items = []
    for person in users:
        source = imported.get(person.id)
        person_roles = roles(db, person)
        if not source and 'tasks.write' not in permissions(db, person):
            continue
        accessible = {task_id for task_id, identifier in responsibilities + assignments if identifier == person.id}
        items.append({'id': person.id, 'name': person.name, 'roles': person_roles,
                      'source': 'Excel ROADMAP' if source else 'Cuenta existente',
                      'aliases': source['aliases'] if source else [],
                      'possible_variants': [names.get(key, key) for key in source.get('possible_variants', [])] if source else [],
                      'task_count': len(accessible),
                      'local_access': person.email.endswith('@participantes.invalid'),
                      'identifier': person.email if team_reader(db, user) or person.id == user.id else None})
    return {'items': items, 'total': len(items), 'imported_count': len(imported)}
