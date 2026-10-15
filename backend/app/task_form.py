"""Workbook classifications and minimal task assignment input."""
from datetime import date
from fastapi import HTTPException
from sqlalchemy import select
from . import models as m
from .service import get_record, audit, serialize
from .task_policy import require_access


def latest_catalog(db):
    return db.scalar(select(m.ImportBatch).where(m.ImportBatch.entity=='task-catalogs', m.ImportBatch.status=='imported').order_by(m.ImportBatch.created_at.desc()).limit(1))


def form_choices(db):
    batch=latest_catalog(db)
    if batch:
        themes=[]
        for item in batch.preview['themes']:
            axis=db.get(m.Axis,item['axis_id'])
            if axis:themes.append({'value':axis.id,'label':axis.name})
        return {'task-themes':sorted(themes,key=lambda r:r['label']), 'offices':[{'value':o['name'],'label':o['name']} for o in batch.preview['offices']]}
    return {'task-themes':[{'value':axis.id,'label':axis.name} for axis in db.scalars(select(m.Axis).order_by(m.Axis.name))], 'offices':[]}


def task_input(db, user, raw, existing=None):
    raw=dict(raw)
    axis_id=raw.pop('axis_id',None)
    if raw.get('office') and (not existing or raw['office'] != existing.office):
        offices={o['value'] for o in form_choices(db)['offices']}
        if not isinstance(raw['office'],str) or raw['office'] not in offices:
            raise HTTPException(422,'Selecciona una oficina del catálogo del Excel.')
    try:
        due=raw.get('due_date',existing.due_date if existing else None)
        due=date.fromisoformat(due) if isinstance(due,str) else due
        if due is None:raise ValueError()
        start=raw.get('start_date',existing.start_date if existing else min(date.today(),due))
        start=date.fromisoformat(start) if isinstance(start,str) else start
        if not isinstance(start,date) or not isinstance(due,date) or start>due:raise ValueError()
    except (ValueError,TypeError):
        raise HTTPException(422,'Indica un plazo válido que no sea anterior al inicio.')
    if not existing:raw.setdefault('start_date',start)
    if not axis_id:
        # Keep existing classification and linked projects when editing. A direct
        # assignment needs no project or theme selected by the person creating it.
        if existing or raw.get('project_id') or raw.get('parent_id'):
            if not existing and raw.get('parent_id') and not raw.get('project_id'):
                parent=get_record(db,m.Task,raw['parent_id']);require_access(db,user,parent)
                raw['project_id']=parent.project_id
            return raw
        axis=db.scalar(select(m.Axis).where(m.Axis.name=='Tareas generales'))
        if not axis:
            axis=m.Axis(name='Tareas generales',modified_by=user.id)
            db.add(axis)
            audit(db,user,'axes',axis,'group_direct_tasks')
        axis_id=axis.id
    if not isinstance(axis_id,str):raise HTTPException(422,'Selecciona una temática válida.')
    axis=get_record(db,m.Axis,axis_id)
    pinned=raw.get('project_id')
    if not pinned and raw.get('parent_id'):
        parent=get_record(db,m.Task,raw['parent_id']);require_access(db,user,parent)
        pinned=parent.project_id
    if not pinned and existing and db.get(m.Project,existing.project_id).axis_id==axis.id:
        pinned=existing.project_id
    if pinned:
        project=get_record(db,m.Project,pinned)
        if project.axis_id!=axis.id:raise HTTPException(422,'La temática debe corresponder a la actividad relacionada.')
    else:
        project=db.scalar(select(m.Project).where(m.Project.group_key=='theme:'+axis.id).with_for_update())
        if not project:
            project=m.Project(title=axis.name,axis_id=axis.id,group_key='theme:'+axis.id,
                              responsible_id=user.id,start_date=start,due_date=due,modified_by=user.id)
            db.add(project);audit(db,user,'projects',project,'group_tasks_by_theme')
    if project.group_key and (start<project.start_date or due>project.due_date):
        before=serialize(project)
        project.start_date=min(start,project.start_date);project.due_date=max(due,project.due_date)
        project.revision+=1;project.modified_by=user.id
        audit(db,user,'projects',project,'task_dates',before)
    raw['project_id']=project.id
    return raw
