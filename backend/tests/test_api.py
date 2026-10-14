import base64
import csv
import io
import unittest
import zipfile
from datetime import date, timedelta
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import event
from app.main import app
from app.db import Base, get_db
from app import models as m
from app.catalog import MODULES
from app.security import hash_password
from app.importer import read_source, STORAGE

PASSWORD = 'Local-pruebas-OGC-123!'


class APITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        @event.listens_for(cls.engine, 'connect')
        def enable_fk(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
        cls.factory = sessionmaker(bind=cls.engine, expire_on_commit=False)
        def db_override():
            with cls.factory() as db:
                yield db
        app.dependency_overrides[get_db] = db_override

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()

    def setUp(self):
        Base.metadata.create_all(self.engine)
        self.client = TestClient(app)
        with self.factory() as db:
            self.admin = m.User(name='Admin ficticio', email='admin@example.invalid', password_hash=hash_password(PASSWORD))
            self.member = m.User(name='Integrante ficticio', email='member@example.invalid', password_hash=hash_password(PASSWORD))
            self.reader = m.User(name='Auditor ficticio', email='reader@example.invalid', password_hash=hash_password(PASSWORD))
            db.add_all([self.admin, self.member, self.reader]); db.flush()
            for user, role_name in [(self.admin,'administrador'),(self.member,'integrante'),(self.reader,'consulta_auditoria')]:
                role = m.Role(name=role_name); db.add(role); db.flush()
                db.add(m.UserRole(user_id=user.id, role_id=role.id))
                for module in MODULES:
                    for action in ['read','write','validate']:
                        permission = db.scalar(select(m.Permission).where(m.Permission.name==module+'.'+action))
                        if not permission:
                            permission = m.Permission(name=module+'.'+action); db.add(permission); db.flush()
                        allowed = role_name=='administrador' or (module not in ['admin','audit'] and (action=='read' or (role_name=='integrante' and action=='write')))
                        if allowed: db.add(m.RolePermission(role_id=role.id,permission_id=permission.id))
            db.commit()
        self.sign_in()
        self.axis = self.create('axes', name='Eje ficticio')
        self.project = self.create('projects', title='Proyecto ficticio', axis_id=self.axis['id'],responsible_id=self.admin.id,
                                   start_date=str(date.today()-timedelta(days=5)), due_date=str(date.today()+timedelta(days=20)))
        self.type = self.create('document-types', name='Carta')

    def tearDown(self):
        self.client.close()
        # Only the disposable in-memory fixture: self references restrict DROP too.
        with self.engine.connect() as connection:
            connection.exec_driver_sql('PRAGMA foreign_keys=OFF')
            connection.commit()
            Base.metadata.drop_all(connection)
            connection.commit()
            connection.exec_driver_sql('PRAGMA foreign_keys=ON')
            connection.commit()

    def sign_in(self,email='admin@example.invalid'):
        self.client.cookies.clear()
        response=self.client.post('/api/auth/login',json={'email':email,'password':PASSWORD})
        self.assertEqual(response.status_code,200,response.text)
        self.client.headers['X-CSRF-Token']=response.json()['csrf_token']
        return response.json()

    def create(self,resource,**kwargs):
        response=self.client.post('/api/'+resource,json=kwargs)
        self.assertEqual(response.status_code,201,response.text)
        return response.json()

    def task(self,**kwargs):
        return self.create('tasks',**({'title':'Tarea ficticia','project_id':self.project['id'],'responsible_id':self.admin.id,
                                     'start_date':str(date.today()),'due_date':str(date.today()+timedelta(days=2))}|kwargs))

    def document(self,**kwargs):
        return self.create('documents',**({'title':'Carta ficticia','number':'TEST-001','year':date.today().year,'document_type_id':self.type['id'],
                      'section':'recibidos','date':str(date.today()),'sender':'Área ficticia','recipient':'OGC demo',
                      'responsible_id':self.admin.id,'project_id':self.project['id']}|kwargs))

    def ready(self,task):
        r=self.client.post('/api/tasks/'+task['id']+'/advance',json={'revision':task['revision'],'progress':100,'comment':'Completo para revisar','request_review':True,
            'evidence': {'title':'Avance de prueba '+task['id'], 'url':'https://drive.google.com/file/d/fictional-ready/view','access_confirmed':True}})
        self.assertEqual(r.status_code,200,r.text)
        task=r.json()
        report=self.client.get('/api/task-updates?task_id='+task['id']).json()['items'][0]
        r=self.client.post('/api/task-updates/'+report['id']+'/review',json={'revision':task['revision'],'status':'validada','note':'Aporte revisado en prueba'})
        self.assertEqual(r.status_code,200,r.text)
        return r.json()

    def evidence(self,task):
        e=self.create('evidence',title='Evidencia ficticia '+task['id'],category='Informe',date=str(date.today()))
        v=self.create('evidence-versions',evidence_id=e['id'],version=1,url='https://drive.google.com/file/d/fictional-test-id/view',access_confirmed=True)
        self.create('evidence-links',evidence_id=e['id'],task_id=task['id'])
        return e,v

    def validate(self,version):
        r=self.client.post('/api/evidence-versions/'+version['id']+'/validate',json={'status':'validada','note':'Permisos y contenido revisados para esta prueba'})
        self.assertEqual(r.status_code,200,r.text)

    def test_unauthenticated(self):
        self.client.cookies.clear()
        for resource in ['tasks','documents','evidence','users','audit']:
            self.assertEqual(self.client.get('/api/'+resource).status_code,401)

    def test_csrf_origin_and_session_cookie(self):
        self.assertIn('HttpOnly',self.client.post('/api/auth/login',json={'email':'admin@example.invalid','password':PASSWORD}).headers['set-cookie'])
        me=self.client.get('/api/auth/me').json();self.client.headers['X-CSRF-Token']=me['csrf_token']
        self.assertEqual(self.client.post('/api/axes',json={'name':'X'},headers={'X-CSRF-Token':''}).status_code,403)
        self.assertEqual(self.client.post('/api/axes',json={'name':'X'},headers={'Origin':'https://evil.invalid'}).status_code,403)
        self.assertEqual(self.client.post('/api/auth/logout').status_code,200)
        self.assertEqual(self.client.get('/api/tasks').status_code,401)

    def test_login_limit(self):
        for _ in range(8): self.assertEqual(self.client.post('/api/auth/login',json={'email':'wrong@example.invalid','password':'bad'}).status_code,401)
        self.assertEqual(self.client.post('/api/auth/login',json={'email':'wrong@example.invalid','password':'bad'}).status_code,429)

    def test_reader_cannot_write(self):
        self.sign_in('reader@example.invalid')
        self.assertEqual(self.client.get('/api/tasks').status_code,200)
        self.assertEqual(self.client.post('/api/axes',json={'name':'No permitido'}).status_code,403)

    def test_member_cannot_edit_others_or_validate(self):
        task=self.task();self.sign_in('member@example.invalid')
        self.assertEqual(self.client.post('/api/tasks/'+task['id']+'/advance',json={'revision':1,'progress':20,'comment':'No autorizado'}).status_code,403)
        self.assertEqual(self.client.patch('/api/tasks/'+task['id'],json={'revision':1,'responsible_id':self.member.id}).status_code,403)
        self.assertEqual(self.client.post('/api/tasks/'+task['id']+'/close',json={'revision':1,'justification':'Una justificación suficiente'}).status_code,403)
        self.assertEqual(self.client.get('/api/users').status_code,403)

    def test_group_assignment_and_mine(self):
        task=self.task();self.create('task-assignments',task_id=task['id'],user_id=self.member.id)
        self.sign_in('member@example.invalid')
        self.assertEqual(self.client.get('/api/tasks?mine=true').json()['total'],1)
        task=self.client.get('/api/tasks/'+task['id']).json()
        r=self.client.post('/api/tasks/'+task['id']+'/advance',json={'revision':task['revision'],'progress':35,'comment':'Avance por integrante asignado',
            'evidence':{'title':'Mi aporte ficticio','url':'https://drive.google.com/file/d/fictional-member/view','access_confirmed':True}})
        self.assertEqual(r.status_code,200,r.text)

    def test_status_and_progress_cannot_bypass_action(self):
        task=self.task()
        for body in [{'revision':1,'status':'cerrada'},{'revision':1,'progress':100}]:
            self.assertEqual(self.client.patch('/api/tasks/'+task['id'],json=body).status_code,422)
        self.assertEqual(self.client.post('/api/tasks/'+task['id']+'/advance',json={'revision':1,'progress':101,'comment':'Invalido'}).status_code,422)

    def test_duplicates_foreign_keys_dates(self):
        doc=self.document()
        self.assertEqual(self.client.post('/api/documents',json={k:v for k,v in doc.items() if k in ['title','number','year','document_type_id','section','date','sender','recipient','responsible_id','project_id']}).status_code,409)
        self.assertEqual(self.client.post('/api/milestones',json={'title':'Hito','project_id':'missing','due_date':str(date.today())}).status_code,409)
        self.assertEqual(self.client.post('/api/projects',json={'title':'Fechas malas','axis_id':self.axis['id'],'responsible_id':self.admin.id,'start_date':'2026-12-01','due_date':'2026-01-01'}).status_code,422)

    def test_search_filters_and_pagination(self):
        self.task(title='Primera tarea',due_date=str(date.today()-timedelta(days=1)),start_date=str(date.today()-timedelta(days=3)))
        self.task(title='Segunda tarea')
        data=self.client.get('/api/tasks?page=1&page_size=1').json()
        self.assertEqual(data['total'],2);self.assertEqual(len(data['items']),1)
        self.assertEqual(self.client.get('/api/tasks?q=Segunda').json()['total'],1)
        self.assertEqual(self.client.get('/api/tasks?overdue=true').json()['total'],1)
        self.assertEqual(self.client.get('/api/tasks?axis_id='+self.axis['id']).json()['total'],2)
        self.assertEqual(self.client.get('/api/tasks?month=14').status_code,422)

    def test_stale_revision(self):
        task=self.task()
        self.assertEqual(self.client.patch('/api/tasks/'+task['id'],json={'revision':1,'title':'Actualizado'}).status_code,200)
        self.assertEqual(self.client.patch('/api/tasks/'+task['id'],json={'revision':1,'title':'Viejo'}).status_code,409)

    def test_dependency_cycles(self):
        a=self.task(title='A');b=self.task(title='B');c=self.task(title='C')
        self.create('task-dependencies',task_id=a['id'],depends_on_id=b['id']);self.create('task-dependencies',task_id=b['id'],depends_on_id=c['id'])
        self.assertEqual(self.client.post('/api/task-dependencies',json={'task_id':c['id'],'depends_on_id':a['id']}).status_code,422)

    def test_close_requires_review_and_evidence_or_authorized_reason(self):
        task=self.task()
        self.assertEqual(self.client.post('/api/tasks/'+task['id']+'/close',json={'revision':1,'justification':'Prueba de justificación autorizada'}).status_code,422)
        task=self.ready(task)
        self.assertEqual(self.client.post('/api/tasks/'+task['id']+'/close',json={'revision':task['revision']}).status_code,422)
        r=self.client.post('/api/tasks/'+task['id']+'/close',json={'revision':task['revision'],'justification':'Excepción autorizada para esta prueba'})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()['status'],'cerrada')

    def test_latest_version_must_be_validated(self):
        task=self.ready(self.task());e,v=self.evidence(task);self.validate(v)
        self.create('evidence-versions',evidence_id=e['id'],version=2,url='https://drive.google.com/file/d/fictional-version-two/view',access_confirmed=True)
        r=self.client.post('/api/tasks/'+task['id']+'/close',json={'revision':task['revision'],'evidence_version_id':v['id']})
        self.assertEqual(r.status_code,422)
        self.assertEqual(self.client.patch('/api/evidence-versions/'+v['id'],json={'revision':1,'url':'https://drive.google.com/file/d/changed/view'}).status_code,409)

    def test_evidence_has_exactly_one_target_and_private_url(self):
        task=self.task();e,v=self.evidence(task)
        self.assertEqual(self.client.post('/api/evidence-links',json={'evidence_id':e['id'],'task_id':task['id'],'project_id':self.project['id']}).status_code,422)
        self.assertEqual(self.client.post('/api/evidence-versions',json={'evidence_id':e['id'],'version':2,'url':'https://public.example.invalid/test'}).status_code,422)

    def test_pending_access_cannot_be_validated(self):
        e=self.create('evidence',title='Permisos pendientes',category='Test',date=str(date.today()))
        v=self.create('evidence-versions',evidence_id=e['id'],version=1,url='https://drive.google.com/file/d/ficticio/view')
        self.assertEqual(self.client.post('/api/evidence-versions/'+v['id']+'/validate',json={'status':'validada','note':'Sin permisos'}).status_code,422)

    def test_document_to_task_to_case_to_evidence_to_close(self):
        received=self.document()
        task=self.task()
        self.create('task-documents',task_id=task['id'],document_id=received['id'])
        sent=self.document(number='TEST-002',section='emitidos',reference_id=received['id'])
        self.create('task-documents',task_id=task['id'],document_id=sent['id'])
        r=self.client.post('/api/documents/'+sent['id']+'/send',json={'revision':1});self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()['approval_status'],'pendiente')
        case=self.create('cases',title='Trámite ficticio',number='EXP-TEST',document_id=sent['id'],responsible_id=self.admin.id,current_department='Área externa ficticia',due_date=str(date.today()+timedelta(days=3)))
        resolution=self.document(number='TEST-003')
        for status in ['revision','firma','derivacion','aprobado']:
            r=self.client.post('/api/cases/'+case['id']+'/stage',json={'revision':case['revision'],'status':status,'department':'Dependencia ficticia','note':'Actuación verificada','resolution_id':resolution['id'] if status=='aprobado' else None})
            self.assertEqual(r.status_code,200,r.text);case=r.json()
        self.assertEqual(self.client.get('/api/documents/'+sent['id']).json()['approval_status'],'aprobado')
        task=self.ready(task);e,v=self.evidence(task);self.validate(v)
        r=self.client.post('/api/tasks/'+task['id']+'/close',json={'revision':task['revision'],'evidence_version_id':v['id']});self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.client.get('/api/task-documents?task_id='+task['id']).json()['total'],2)
        self.assertEqual(self.client.get('/api/case-events?case_id='+case['id']).json()['total'],4)

    def test_meeting_to_agreement_to_task_to_close_idempotent(self):
        meeting=self.create('meetings',title='Reunión ficticia',date='2026-10-13T10:00:00',agenda='Compromisos de prueba',location='Demo',responsible_id=self.admin.id,project_id=self.project['id'])
        agreement=self.create('agreements',title='Acuerdo ficticio',meeting_id=meeting['id'],project_id=self.project['id'],responsible_id=self.admin.id,due_date=str(date.today()+timedelta(days=5)))
        endpoint='/api/agreements/'+agreement['id']+'/task'
        first=self.client.post(endpoint,json={'revision':1});self.assertEqual(first.status_code,200,first.text)
        second=self.client.post(endpoint,json={'revision':1});self.assertEqual(second.json()['id'],first.json()['id'])
        task=self.ready(first.json());e,v=self.evidence(task);self.validate(v)
        self.assertEqual(self.client.post('/api/tasks/'+task['id']+'/close',json={'revision':task['revision'],'evidence_version_id':v['id']}).status_code,200)
        self.assertEqual(self.client.get('/api/agreements/'+agreement['id']).json()['status'],'cumplido')

    def test_dependents_and_children_prevent_close(self):
        a=self.ready(self.task(title='A'));b=self.task(title='B')
        self.create('task-dependencies',task_id=a['id'],depends_on_id=b['id'])
        self.assertEqual(self.client.post('/api/tasks/'+a['id']+'/close',json={'revision':a['revision'],'justification':'Prueba de excepción autorizada'}).status_code,422)

    def test_recurrence_creates_next_task_once(self):
        task=self.ready(self.task(recurrence='mensual'))
        r=self.client.post('/api/tasks/'+task['id']+'/close',json={'revision':task['revision'],'justification':'Cierre autorizado en prueba mensual'})
        self.assertEqual(r.status_code,200,r.text)
        items=self.client.get('/api/tasks').json()['items'];self.assertEqual(len(items),2)
        self.assertEqual(sum(t['recurrence_source_id']==task['id'] for t in items),1)

    def test_os_conformity_requires_presentation(self):
        order=self.create('service-orders',title='Orden ficticia',number='OS-TEST',provider='Prestador ficticio',responsible_id=self.admin.id,start_date=str(date.today()),due_date=str(date.today()+timedelta(days=5)))
        item=self.create('deliverables',title='Informe ficticio',service_order_id=order['id'],responsible_id=self.admin.id,due_date=str(date.today()+timedelta(days=3)))
        endpoint='/api/deliverables/'+item['id']+'/review'
        self.assertEqual(self.client.post(endpoint,json={'revision':1,'status':'conforme','note':'Revisado'}).status_code,422)
        doc=self.document()
        r=self.client.patch('/api/deliverables/'+item['id'],json={'revision':1,'presentation_document_id':doc['id']});item=r.json()
        self.assertEqual(self.client.post(endpoint,json={'revision':item['revision'],'status':'conforme','note':'Presentación y contenido verificados'}).status_code,200)

    def test_quality_needs_source_and_revalidation(self):
        model=self.create('quality-models',title='Modelo ficticio',version='Demo')
        self.assertEqual(model['status'],'pendiente_validacion')
        self.assertEqual(self.client.post('/api/quality-models/'+model['id']+'/validate',json={'revision':1}).status_code,422)
        model=self.client.patch('/api/quality-models/'+model['id'],json={'revision':1,'source_url':'https://reference.example.invalid/demo'}).json()
        model=self.client.post('/api/quality-models/'+model['id']+'/validate',json={'revision':model['revision']}).json()
        self.assertEqual(model['status'],'validado')
        model=self.client.patch('/api/quality-models/'+model['id'],json={'revision':model['revision'],'version':'Demo-2'}).json()
        self.assertEqual(model['status'],'pendiente_validacion')

    def test_audit_and_password_redaction_and_revoke(self):
        users=self.client.get('/api/users').json();self.assertNotIn('password_hash',str(users))
        self.task()
        rows=self.client.get('/api/audit').json()['items'];self.assertTrue(any(r['entity']=='tasks' for r in rows))
        self.assertNotIn(PASSWORD,str(rows));self.assertNotIn('password_hash',str(rows))
        assignment=self.client.get('/api/user-roles?user_id='+self.admin.id).json()['items'][0]
        self.assertEqual(self.client.post('/api/admin/user-roles/'+assignment['id']+'/revoke',json={}).status_code,422)

    def test_dashboard_and_csv_formula_escape(self):
        self.task(title='=HYPERLINK("ficticio")')
        response=self.client.get('/api/reports/tasks.csv');self.assertEqual(response.status_code,200)
        self.assertIn("'=HYPERLINK",response.text)
        data=self.client.get('/api/dashboard').json();self.assertEqual(data['task_count'],1);self.assertEqual(data['pending'],1)

    def test_import_preview_commit_trace_duplicates(self):
        content='nombre,numero,fecha\nDocumento importado,IMPORT-001,'+str(date.today())+'\n'
        body={'filename':'ficticio.csv','content_base64':base64.b64encode(content.encode()).decode(),'entity':'documents',
              'mapping':{'title':'nombre','number':'numero','date':'fecha'},'constants':{'year':date.today().year,'document_type_id':self.type['id'],'section':'recibidos','sender':'Área ficticia','recipient':'OGC demo','responsible_id':self.admin.id}}
        r=self.client.post('/api/import/preview',json=body);self.assertEqual(r.status_code,200,r.text)
        preview=r.json();self.assertEqual(preview['error_count'],0)
        backup=STORAGE/(preview['sha256']+'.csv');self.assertEqual(backup.read_bytes(),content.encode())
        r=self.client.post('/api/import/commit/'+preview['id'],json={});self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()['imported'],1)
        self.assertEqual(self.client.get('/api/import-sources').json()['total'],1)
        self.assertEqual(self.client.post('/api/import/commit/'+preview['id'],json={}).status_code,409)

    def test_import_errors_block_commit(self):
        content='title,number\nDoc,ERR-001\n'
        body={'filename':'errors.csv','content_base64':base64.b64encode(content.encode()).decode(),'entity':'documents','mapping':{'title':'title','number':'number'}}
        r=self.client.post('/api/import/preview',json=body);self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()['error_count'],1)
        self.assertEqual(self.client.post('/api/import/commit/'+r.json()['id'],json={}).status_code,409)

    def test_xlsx_sheet_and_external_links_inspection(self):
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w') as z:
            z.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="REGISTRO DIGITAL" sheetId="1" r:id="rId1"/></sheets></workbook>')
            z.writestr('xl/_rels/workbook.xml.rels','<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
            z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row><c r="A1" t="inlineStr"><is><t>NOMBRE</t></is></c></row><row><c r="A2" t="inlineStr"><is><t>Demo</t></is></c></row></sheetData></worksheet>')
            z.writestr('xl/worksheets/_rels/sheet1.xml.rels','<Relationships><Relationship Id="rId2" Target="https://drive.google.com/fictional-sheet" TargetMode="External"/></Relationships>')
        headers,rows,sheet,sheets,links=read_source('test.xlsx',output.getvalue())
        self.assertEqual(headers,['nombre']);self.assertEqual(rows[0][1]['nombre'],'Demo');self.assertEqual(sheet,'REGISTRO DIGITAL');self.assertFalse(links[0]['reviewed'])


class MigrationTest(unittest.TestCase):
    def test_frozen_sqlite_migration(self):
        engine=create_engine('sqlite://')
        path=Path(__file__).resolve().parents[2]/'database/migrations/001_initial_sqlite.sql'
        with engine.begin() as db:
            for stmt in path.read_text(encoding='utf-8').split(';'):
                if stmt.strip():db.exec_driver_sql(stmt)
            for stmt in path.with_name('002_task_collaboration_sqlite.sql').read_text(encoding='utf-8').split(';'):
                if stmt.strip():db.exec_driver_sql(stmt)
            for stmt in path.with_name('003_task_form_sqlite.sql').read_text(encoding='utf-8').split(';'):
                if stmt.strip():db.exec_driver_sql(stmt)
            tables=db.exec_driver_sql("SELECT count(*) FROM sqlite_master WHERE type='table'").scalar()
            self.assertEqual(tables,len(Base.metadata.tables))
        engine.dispose()


if __name__=='__main__':unittest.main()
