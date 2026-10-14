import unittest
from unittest.mock import patch
from pathlib import Path
from datetime import date
from sqlalchemy import create_engine, MetaData, Table, select, func
from sqlalchemy.orm import sessionmaker
from app import models as m
from app import seed as bootstrap
from app.security import permissions


class CollaborationMigrationTest(unittest.TestCase):
    def apply(self, db, name):
        path=Path(__file__).resolve().parents[2]/'database/migrations'/name
        for statement in path.read_text(encoding='utf-8').split(';'):
            if statement.strip(): db.exec_driver_sql(statement)

    def test_additive_migration_preserves_history_and_recovers_creator_not_last_editor(self):
        engine=create_engine('sqlite://')
        with engine.begin() as db:
            db.exec_driver_sql('PRAGMA foreign_keys=ON')
            self.apply(db,'001_initial_sqlite.sql')
            meta=MetaData()
            tables={name:Table(name,meta,autoload_with=db) for name in ['users','roles','axes','projects','tasks','task_assignments','audit']}
            common={'created_at':m.now(),'updated_at':m.now(),'revision':1}
            for identifier in ['creator','editor']:
                db.execute(tables['users'].insert().values(**common,id=identifier,name=identifier+' demo',email=identifier+'@example.invalid',password_hash='ficticio',active=True,department='OGC'))
            for name in ['jefatura','coordinador','consulta_auditoria']:
                db.execute(tables['roles'].insert().values(**common,id=name,name=name))
            db.execute(tables['axes'].insert().values(**common,id='axis',name='Eje demo',color='#18847c'))
            db.execute(tables['projects'].insert().values(**common,id='project',title='Proyecto demo',axis_id='axis',responsible_id='creator',start_date=date.today(),due_date=date.today(),status='en_progreso'))
            db.execute(tables['tasks'].insert().values(**common,id='task',title='Actividad demo',project_id='project',responsible_id='creator',modified_by='editor',start_date=date.today(),due_date=date.today(),status='en_progreso',priority='media',progress=65,recurrence='ninguna'))
            db.execute(tables['task_assignments'].insert().values(**common,id='assignment',task_id='task',user_id='editor',modified_by='editor'))
            for entity,identifier in [('tasks','task'),('task-assignments','assignment')]:
                db.execute(tables['audit'].insert().values(id=m.uid(),actor_id='creator',entity=entity,record_id=identifier,action='create',created_at=m.now()))
            self.apply(db,'002_task_collaboration_sqlite.sql')
            row=db.exec_driver_sql('SELECT created_by, modified_by, progress FROM tasks').one()
            self.assertEqual(tuple(row),('creator','editor',65))
            self.assertEqual(db.exec_driver_sql('SELECT assigned_by FROM task_assignments').scalar(),'creator')
            self.assertEqual(db.exec_driver_sql('SELECT count(*) FROM audit').scalar(),2)
            self.assertEqual(db.exec_driver_sql('SELECT count(*) FROM task_update_reviews').scalar(),0)
            grants=db.exec_driver_sql('SELECT r.name, p.name FROM role_permissions rp JOIN roles r ON r.id=rp.role_id JOIN permissions p ON p.id=rp.permission_id').all()
            self.assertEqual(set(tuple(row) for row in grants),{('jefatura','tasks.supervise'),('consulta_auditoria','tasks.team_read')})
            self.assertEqual(db.exec_driver_sql('PRAGMA foreign_key_check').all(),[])
        engine.dispose()

    def test_fresh_seed_after_002_grants_roles_and_is_idempotent(self):
        engine=create_engine('sqlite://')
        with engine.begin() as db:
            self.apply(db,'001_initial_sqlite.sql');self.apply(db,'002_task_collaboration_sqlite.sql');self.apply(db,'003_task_form_sqlite.sql')
        factory=sessionmaker(bind=engine,expire_on_commit=False)
        with patch.object(bootstrap,'engine',engine), patch.object(bootstrap,'SessionLocal',factory), patch.object(bootstrap.command,'upgrade'), patch.object(Path,'write_text'), patch.object(bootstrap.settings,'demo_password','Ficticio-pruebas-2026!'):
            bootstrap.seed();bootstrap.seed()
        with factory() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(m.User)),5)
            self.assertEqual(db.scalar(select(func.count()).select_from(m.Task)),8)
            chief=db.scalar(select(m.User).where(m.User.email=='jefatura@example.invalid'))
            member=db.scalar(select(m.User).where(m.User.email=='integrante@example.invalid'))
            coordinator=db.scalar(select(m.User).where(m.User.email=='coordinador@example.invalid'))
            self.assertIn('tasks.supervise',permissions(db,chief))
            self.assertNotIn('tasks.supervise',permissions(db,member))
            self.assertNotIn('tasks.supervise',permissions(db,coordinator))
            self.assertEqual(db.scalar(select(func.count()).select_from(m.Task).where(m.Task.created_by==chief.id)),8)
        engine.dispose()
