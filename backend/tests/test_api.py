import base64
import csv
import io
import unittest
import zipfile
from datetime import date, datetime, timedelta
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
            self.chief = m.User(name='Jefatura ficticia', email='reviewer@example.invalid', password_hash=hash_password(PASSWORD))
            db.add(self.chief); db.flush()
            admin_role = db.scalar(select(m.Role).where(m.Role.name == 'administrador'))
            db.add(m.UserRole(user_id=self.chief.id, role_id=admin_role.id))
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
        self.sign_in('reviewer@example.invalid')
        r=self.client.post('/api/task-updates/'+report['id']+'/review',json={'revision':task['revision'],'status':'validada','note':'Aporte revisado en prueba'})
        self.assertEqual(r.status_code,200,r.text)
        self.sign_in()
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
        r=self.client.post('/api/documents/'+sent['id']+'/send',json={'revision':1,'status':'enviado_digital','sent_date':str(date.today())});self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()['approval_status'],'pendiente')
        case=self.create('cases',title='Trámite ficticio',number='EXP-TEST',document_id=sent['id'],responsible_id=self.admin.id,current_department='Área externa ficticia',due_date=str(date.today()+timedelta(days=3)))
        resolution=self.document(number='TEST-003')
        for status in ['revision','firma','derivacion','aprobado']:
            r=self.client.post('/api/cases/'+case['id']+'/stage',json={'revision':case['revision'],'status':status,'department':'Dependencia ficticia','note':'Actuación verificada','resolution_id':resolution['id'] if status=='aprobado' else None})
            self.assertEqual(r.status_code,200,r.text);case=r.json()
        sent_record = self.client.get('/api/documents/'+sent['id']).json()
        self.assertEqual(sent_record['approval_status'], 'pendiente')
        self.assertEqual(sent_record['document_status'], 'enviado_digital')
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


    def test_meeting_range_includes_entire_last_day(self):
        meeting = self.create('meetings', title='Reunión del día final', date='2026-10-14T10:00:00',
                              agenda='Agenda ficticia', location='Sala ficticia',
                              responsible_id=self.admin.id, project_id=self.project['id'])
        result = self.client.get('/api/meetings', params={'from': '2026-10-14', 'to': '2026-10-14'}).json()
        self.assertEqual([r['id'] for r in result['items']], [meeting['id']])
        self.assertEqual(self.client.get('/api/meetings', params={'to': '2026-10-13'}).json()['total'], 0)
        self.assertEqual(self.client.get('/api/meetings', params={'from': '2026-10-15', 'to': '2026-10-14'}).status_code, 422)
        self.assertEqual(meeting['date'], '2026-10-14T10:00:00')

    def test_relation_search_uses_visible_names_and_respects_task_scope(self):
        result = self.client.get('/api/user-roles', params={'q': 'Admin ficticio'}).json()
        self.assertEqual(result['total'], 1)
        self.assertEqual(self.client.get('/api/role-permissions', params={'q': 'administrador'}).json()['total'], 33)
        self.assertEqual(self.client.get('/api/user-roles', params={'q': 'ZZZ-NO-EXISTE'}).json()['total'], 0)
        hidden = self.task(title='Nombre reservado para administración')
        self.sign_in('member@example.invalid')
        result = self.client.get('/api/task-assignments', params={'q': hidden['title']}).json()
        self.assertEqual(result['total'], 0)

    def test_audit_instants_include_utc_zone_without_changing_calendar_dates(self):
        timestamp = datetime.fromisoformat(self.project['updated_at'])
        self.assertIsNotNone(timestamp.tzinfo)
        self.assertEqual(timestamp.utcoffset(), timedelta(0))
        self.assertEqual(self.project['start_date'], str(date.today() - timedelta(days=5)))

    def test_validation_errors_are_spanish_and_do_not_include_raw_input(self):
        response = self.client.post('/api/meetings', json={'title': 'Reunión incompleta'})
        self.assertEqual(response.status_code, 422)
        errors = response.json()['detail']
        self.assertTrue(any(error['label'] == 'Agenda' for error in errors))
        self.assertTrue(all(error['msg'] == 'Este campo es obligatorio.' for error in errors))
        self.assertTrue(all('input' not in error and 'url' not in error for error in errors))
        response = self.client.post('/api/auth/login', json={'email': 'a', 'password': ''})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn('Field required', response.text)

    def test_import_batch_metadata_export_is_available_only_to_admin_readers(self):
        with self.factory() as db:
            db.add(m.ImportBatch(filename='Fuente ficticia.csv', sheet='CSV', sha256='a' * 64, backup_path='backup.csv',
                                 entity='documents', mapping={}, preview={'rows': [{'private': 'detalle de prueba'}]},
                                 modified_by=self.admin.id))
            db.commit()
        response = self.client.get('/api/reports/import-batches.csv')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn('Fuente ficticia.csv', response.text)
        self.assertIn('Huella del archivo', response.text)
        self.assertNotIn('detalle de prueba', response.text)
        self.sign_in('member@example.invalid')
        self.assertEqual(self.client.get('/api/reports/import-batches.csv').status_code, 403)

    def document_data(self, **changes):
        return {'title': 'Documento ficticio', 'year': 2026, 'document_type_id': self.type['id'],
                'section': 'emitidos', 'date': '2026-10-14', 'sender': 'OGC ficticia',
                'recipient': 'Área ficticia', 'responsible_id': self.admin.id, **changes}

    def test_emitted_workflow_records_exact_medium_dates_followup_and_exports(self):
        for state in ['enviado_digital', 'enviado_fisico', 'enviado_fisico_y_digital']:
            doc = self.create('documents', **self.document_data(automatic_number=True))
            self.assertEqual(doc['document_status'], 'por_inicio')
            self.assertIsNone(doc['sent_date'])
            missing_medium = self.client.post('/api/documents/'+doc['id']+'/send', json={'revision':doc['revision']})
            self.assertEqual(missing_medium.status_code, 422)
            result = self.client.post('/api/documents/'+doc['id']+'/send', json={
                'revision':doc['revision'], 'status':state, 'sent_date':'2026-10-12'})
            self.assertEqual(result.status_code, 200, result.text)
            sent = result.json()
            self.assertEqual((sent['document_status'], sent['sent_date']), (state, '2026-10-12'))
            result = self.client.patch('/api/documents/'+doc['id'], json={
                'revision':sent['revision'], 'receipt_number':'CARGO-123', 'priority':'alta',
                'followup_frequency':'quincenal', 'comments':'Esperar respuesta del área',
                'email_url':'https://mail.google.com/mail/u/0/#sent/example', 'attended':True})
            self.assertEqual(result.status_code, 200, result.text)
            self.assertEqual(result.json()['receipt_number'], 'CARGO-123')
            filtered = self.client.get('/api/documents', params={'preparation_status':state}).json()['items']
            self.assertEqual([item['id'] for item in filtered], [doc['id']])
        self.assertEqual(self.client.get('/api/dashboard').json()['pending_documents'], 0)
        export = self.client.get('/api/reports/documents.csv').text
        self.assertIn('Estado del documento', export)
        self.assertIn('enviado_fisico_y_digital', export)
        self.assertNotIn('Aprobación', export)
        self.assertNotIn('Atención del documento recibido', export)

    def test_document_workflow_rejects_inconsistent_dates_and_type_states(self):
        for changes in [
            {'preparation_status':'enviado_digital'},
            {'preparation_status':'en_redaccion','sent_date':'2026-10-12'},
            {'preparation_status':'aprobado'},
        ]:
            response = self.client.post('/api/documents', json=self.document_data(automatic_number=True, **changes))
            self.assertEqual(response.status_code, 422, response.text)
        doc = self.create('documents', **self.document_data(automatic_number=True, preparation_status='en_redaccion'))
        response = self.client.patch('/api/documents/'+doc['id'], json={
            'revision':doc['revision'], 'preparation_status':'enviado_fisico_y_digital','sent_date':'2026-10-12'})
        self.assertEqual(response.status_code, 200, response.text)
        sent = response.json()
        response = self.client.patch('/api/documents/'+doc['id'], json={
            'revision':sent['revision'], 'preparation_status':'en_redaccion'})
        self.assertEqual(response.status_code, 422)
        minutes_type = self.create('document-types', name='Acta de reunión')
        response = self.client.post('/api/documents', json=self.document_data(automatic_number=True,
            document_type_id=minutes_type['id'], preparation_status='programada'))
        self.assertEqual(response.status_code, 201, response.text)
        received = self.document(intake_format='ambos', notebook_number='CUADERNO-42')
        self.assertEqual(received['document_status'], 'pendiente_atencion')
        self.assertEqual(self.client.get('/api/dashboard').json()['pending_documents'], 1)
        self.assertEqual(self.client.get('/api/documents', params={'axis_id':self.axis['id']}).status_code, 200)

    def test_document_number_preview_does_not_reserve_and_series_restart_by_year(self):
        params = {'document_type_id': self.type['id'], 'year': 2026}
        for _ in range(2):
            self.assertEqual(self.client.get('/api/documents/next-number', params=params).json()['number'], 'CARTA N° 001-2026-UNAJMA-OGC')
        first = self.create('documents', **self.document_data(automatic_number=True))
        second = self.create('documents', **self.document_data(automatic_number=True))
        self.assertEqual(first['number'], 'CARTA N° 001-2026-UNAJMA-OGC')
        self.assertEqual(second['number'], 'CARTA N° 002-2026-UNAJMA-OGC')
        next_year = self.create('documents', **self.document_data(year=2027, date='2027-01-01'))
        self.assertEqual(next_year['number'], 'CARTA N° 001-2027-UNAJMA-OGC')
        for type_name, prefix, suffix in [('Carta múltiple', 'CARTA MÚLTIPLE', 'UNAJMA-OGC'),
                                         ('Informe', 'INFORME', 'UNAJMA-OGC'),
                                         ('Informe técnico', 'INFORME TÉCNICO', 'UNAJMA/OGC'),
                                         ('Oficio', 'OFICIO', 'UNAJMA-OGC'),
                                         ('Acta de reunión', 'ACTA DE REUNIÓN', 'UNAJMA-OGC-SGCI')]:
            typ = self.create('document-types', name=type_name)
            record = self.create('documents', **self.document_data(document_type_id=typ['id']))
            self.assertEqual(record['number'], f'{prefix} N° 001-2026-{suffix}')

    def test_document_sequence_continues_reference_and_existing_alias_numbers(self):
        with self.factory() as db:
            db.add(m.DocumentSequence(series='carta', year=2026, last_number=500))
            db.commit()
        self.create('documents', **self.document_data(section='recibidos', number='CARTA N° 900-2026-OTRA-ENTIDAD'))
        self.assertEqual(self.create('documents', **self.document_data())['number'], 'CARTA N° 501-2026-UNAJMA-OGC')
        self.create('documents', **self.document_data(number='CARTA N° 520-2026-UNAJMA-OGC'))
        alias = self.create('document-types', name='Carta simple')
        automatic = self.create('documents', **self.document_data(document_type_id=alias['id'], automatic_number=True, number='IGNORAR ESTA SUGERENCIA'))
        self.assertEqual(automatic['number'], 'CARTA N° 521-2026-UNAJMA-OGC')
        self.assertEqual(self.create('documents', **self.document_data())['number'], 'CARTA N° 522-2026-UNAJMA-OGC')

    def test_document_link_is_saved_atomically_and_edit_preserves_version_history(self):
        url = 'https://docs.google.com/document/d/ficticio-v1/edit'
        record = self.create('documents', **self.document_data(url='  ' + url + '  ', access_confirmed=True))
        self.assertEqual((record['url'], record['version'], record['access_confirmed']), (url, 1, True))
        response = self.client.patch('/api/documents/' + record['id'], json={'revision': record['revision'], 'url': url, 'access_confirmed': True})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['version'], 1)
        new_url = 'https://www.unajma.edu.pe/transparencia/documento-ficticio.pdf'
        response = self.client.patch('/api/documents/' + record['id'], json={'revision': response.json()['revision'], 'url': new_url, 'access_confirmed': False})
        self.assertEqual(response.status_code, 200, response.text)
        edited = response.json()
        self.assertEqual((edited['number'], edited['url'], edited['version']), (record['number'], new_url, 2))
        versions = self.client.get('/api/document-versions', params={'document_id': record['id']}).json()['items']
        self.assertEqual({(v['version'], v['url']) for v in versions}, {(1, url), (2, new_url)})
        self.assertIn(new_url, self.client.get('/api/reports/documents.csv').text)
        self.assertEqual(self.client.get('/api/documents/' + record['id']).json()['url'], new_url)

    def test_invalid_document_links_or_failed_insert_do_not_consume_number(self):
        for url in ['javascript:alert(1)', 'https://unajma.edu.pe.evil.invalid/doc', 'https://user:pass@docs.google.com/doc', 'http://drive.google.com/doc']:
            response = self.client.post('/api/documents', json=self.document_data(url=url))
            self.assertEqual(response.status_code, 422, response.text)
        response = self.client.post('/api/documents', json=self.document_data(responsible_id='no-existe'))
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(self.create('documents', **self.document_data())['number'], 'CARTA N° 001-2026-UNAJMA-OGC')
        metadata = self.client.get('/api/meta').json()['documents']['fields']
        self.assertTrue(any(field['key'] == 'url' for field in metadata))

    def test_received_and_normative_documents_keep_original_numbers_and_permissions(self):
        response = self.client.post('/api/documents', json=self.document_data(automatic_number=False))
        self.assertEqual(response.status_code, 422)
        response = self.client.post('/api/documents', json=self.document_data(section='recibidos', automatic_number=True))
        self.assertEqual(response.status_code, 422)
        response = self.client.post('/api/documents', json=self.document_data(section='recibidos'))
        self.assertEqual(response.status_code, 422)
        plan = self.create('document-types', name='Plan')
        params = {'document_type_id': plan['id'], 'year': 2026}
        self.assertFalse(self.client.get('/api/documents/next-number', params=params).json()['automatic'])
        record = self.create('documents', **self.document_data(document_type_id=plan['id'], section='normativos', number='UNAJMA.PL.A03.05.01.01'))
        self.assertEqual(record['number'], 'UNAJMA.PL.A03.05.01.01')
        self.sign_in('reader@example.invalid')
        self.assertEqual(self.client.get('/api/documents/next-number', params=params).status_code, 403)

    def test_document_destinations_use_existing_catalog_and_sender_follows_remitter(self):
        with self.factory() as db:
            db.add(m.ImportBatch(filename='Registro ficticio.xlsx', sheet='Listas', sha256='f'*64, backup_path='ficticio.xlsx',
                                 entity='document-catalogs', status='imported', mapping={},
                                 preview={'recipients': ['Rectorado', 'DIGA', 'SUNEDU']}, modified_by=self.admin.id))
            db.commit()
        options = self.client.get('/api/lookups').json()['document-recipients']
        self.assertEqual([item['value'] for item in options], ['Rectorado', 'DIGA', 'SUNEDU'])
        data = self.document_data(recipient='Rectorado', axis_id=self.axis['id'])
        data.pop('sender')
        document = self.create('documents', **data)
        self.assertEqual(document['sender'], self.admin.name)
        self.assertEqual(document['axis_id'], self.axis['id'])
        self.assertIsNone(document['project_id'])
        response = self.client.post('/api/documents', json={**data, 'recipient': 'Oficina inventada'})
        self.assertEqual(response.status_code, 422)
        response = self.client.post('/api/documents', json={**data, 'recipient': ['Rectorado']})
        self.assertEqual(response.status_code, 422)
        response = self.client.post('/api/documents', json={**data, 'responsible_id': {'id': self.admin.id}})
        self.assertEqual(response.status_code, 422)
        response = self.client.patch('/api/documents/' + document['id'], json={'revision': document['revision'], 'responsible_id': self.member.id})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['sender'], self.member.name)
        self.assertEqual(response.json()['number'], document['number'])

    def test_document_edit_preserves_legacy_destination_and_project_without_exposing_them(self):
        document = self.create('documents', **self.document_data(project_id=self.project['id']))
        with self.factory() as db:
            db.add(m.ImportBatch(filename='Catálogo ficticio', sheet='Listas', sha256='f'*64, backup_path='ficticio',
                                 entity='document-catalogs', status='imported', mapping={}, preview={'recipients':['Rectorado']}, modified_by=self.admin.id))
            db.commit()
        response = self.client.patch('/api/documents/' + document['id'], json={'revision': document['revision'], 'title':'Asunto actualizado', 'recipient':document['recipient']})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['project_id'], self.project['id'])
        self.assertEqual(response.json()['recipient'], document['recipient'])


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
            for stmt in path.with_name('004_document_registry_sqlite.sql').read_text(encoding='utf-8').split(';'):
                if stmt.strip():db.exec_driver_sql(stmt)
            for stmt in path.with_name('005_document_axis_sqlite.sql').read_text(encoding='utf-8').split(';'):
                if stmt.strip():db.exec_driver_sql(stmt)
            for migration in ['006_document_workflow_sqlite.sql', '007_chief_administration_sqlite.sql', '008_evidence_files_sqlite.sql', '009_cloud_accounts_sqlite.sql', '010_cloud_configuration_sqlite.sql']:
                for stmt in path.with_name(migration).read_text(encoding='utf-8').split(';'):
                    if stmt.strip(): db.exec_driver_sql(stmt)
            tables=db.exec_driver_sql("SELECT count(*) FROM sqlite_master WHERE type='table'").scalar()
            self.assertEqual(tables,len(Base.metadata.tables))
        engine.dispose()


if __name__=='__main__':unittest.main()
