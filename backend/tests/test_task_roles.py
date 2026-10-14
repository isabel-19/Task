import unittest
from datetime import date, timedelta
from sqlalchemy import select
import test_api
from app import models as m


class TaskRolesTest(unittest.TestCase):
    setUpClass = classmethod(test_api.APITest.setUpClass.__func__)
    tearDownClass = classmethod(test_api.APITest.tearDownClass.__func__)
    setUp = test_api.APITest.setUp
    tearDown = test_api.APITest.tearDown
    sign_in = test_api.APITest.sign_in
    create = test_api.APITest.create
    task = test_api.APITest.task
    evidence = test_api.APITest.evidence

    def submit(self, task, progress, label):
        response = self.client.post('/api/tasks/'+task['id']+'/advance', json={
            'revision':task['revision'], 'progress':progress, 'comment':'Aporte ficticio '+label,
            'evidence':{'title':'Evidencia de prueba '+label, 'url':'https://drive.google.com/file/d/fictional-'+label+'/view', 'access_confirmed':True}})
        self.assertEqual(response.status_code,200,response.text)
        report = self.client.get('/api/task-updates?task_id='+task['id']).json()['items'][0]
        return response.json(), report

    def review(self, task, report, status='validada'):
        response = self.client.post('/api/task-updates/'+report['id']+'/review', json={'revision':task['revision'], 'status':status, 'note':'Revisión ficticia '+status})
        self.assertEqual(response.status_code,200,response.text)
        return response.json()

    def test_privacy_across_list_detail_lookup_csv_dashboard_alerts_evidence(self):
        hidden = self.task(title='Reservada ficticia', due_date=str(date.today()))
        hidden_evidence, hidden_version = self.evidence(hidden)
        shared = self.task(title='Compartida ficticia', responsible_id=self.member.id)
        self.sign_in('member@example.invalid')
        for suffix in ['', '?mine=false', '?scope=personal']:
            response=self.client.get('/api/tasks'+suffix)
            self.assertEqual(response.status_code,200,response.text)
            self.assertEqual([r['id'] for r in response.json()['items']],[shared['id']])
        self.assertEqual(self.client.get('/api/tasks?scope=team').status_code,403)
        self.assertEqual(self.client.get('/api/tasks/'+hidden['id']).status_code,403)
        self.assertEqual(self.client.get('/api/task-updates?task_id='+hidden['id']).json()['total'],0)
        self.assertEqual(self.client.get('/api/evidence/'+hidden_evidence['id']).status_code,403)
        self.assertEqual(self.client.get('/api/evidence-versions/'+hidden_version['id']).status_code,403)
        self.assertNotIn(hidden['id'],str(self.client.get('/api/lookups').json()))
        self.assertNotIn(hidden['title'],self.client.get('/api/reports/tasks.csv').text)
        self.assertEqual(self.client.get('/api/dashboard').json()['task_count'],1)
        self.assertNotIn(hidden['id'],str(self.client.get('/api/alerts').json()))

    def test_member_assigns_to_another_member_and_retains_authorship(self):
        self.sign_in('member@example.invalid')
        task = self.task(title='Asignación entre integrantes', responsible_id=self.admin.id)
        self.assertEqual(task['created_by'],self.member.id)
        self.assertFalse(task['can_advance'])
        self.assertTrue(task['can_edit'])
        self.assertEqual(self.client.get('/api/tasks?scope=assigned').json()['total'],1)
        self.assertEqual(self.client.get('/api/tasks?scope=received').json()['total'],0)
        assignment=self.create('task-assignments',task_id=task['id'],user_id=self.member.id)
        self.assertEqual(assignment['assigned_by'],self.member.id)
        self.assertEqual(self.client.get('/api/tasks?scope=joint').json()['total'],1)
        self.assertEqual(self.client.patch('/api/tasks/'+task['id'],json={'revision':2,'created_by':self.admin.id}).status_code,422)
        self.assertEqual(self.client.patch('/api/task-assignments/'+assignment['id'],json={'revision':1,'assigned_by':self.admin.id}).status_code,422)

    def test_group_reports_do_not_overwrite_each_other_and_chief_validates(self):
        task=self.task(member_ids=[self.member.id])
        self.assertEqual(len(task['participants']),2)
        task, first=self.submit(task,100,'responsable')
        self.assertEqual(task['reported_progress'],50)
        self.assertEqual(task['progress'],0)
        task=self.review(task,first)
        self.assertEqual(task['progress'],50)
        export=self.client.get('/api/reports/tasks.csv').text
        self.assertIn('Participantes',export)
        self.assertIn(self.member.name,export)
        self.sign_in('member@example.invalid')
        task, second=self.submit(task,60,'integrante')
        self.assertEqual(task['reported_progress'],80)
        self.assertEqual(task['progress'],50)
        self.assertEqual(self.client.post('/api/task-updates/'+second['id']+'/review',json={'revision':task['revision'],'status':'validada','note':'No puedo validar'}).status_code,403)
        self.sign_in()
        task=self.review(task,second,'observada')
        self.assertEqual(task['progress'],50)
        self.sign_in('member@example.invalid')
        task, third=self.submit(task,100,'correccion')
        self.assertEqual(task['reported_progress'],100)
        self.assertEqual(task['status'],'en_revision')
        self.sign_in()
        self.assertEqual(self.client.post('/api/tasks/'+task['id']+'/close',json={'revision':task['revision'],'justification':'Cierre aún pendiente de validación'}).status_code,422)
        task=self.review(task,third)
        self.assertEqual(task['progress'],100)
        self.assertTrue(task['all_complete'])
        self.assertEqual(self.client.get('/api/task-updates?task_id='+task['id']).json()['total'],3)
        self.assertEqual(self.client.get('/api/task-update-reviews?scope=team').json()['total'],3)
        closed=self.client.post('/api/tasks/'+task['id']+'/close',json={'revision':task['revision'],'evidence_version_id':third['evidence_version_id']})
        self.assertEqual(closed.status_code,200,closed.text)

    def test_evidence_required_current_and_owned_and_review_cannot_repeat(self):
        task=self.task()
        missing={'revision':1,'progress':30,'comment':'Sin evidencia'}
        self.assertEqual(self.client.post('/api/tasks/'+task['id']+'/advance',json=missing).status_code,422)
        self.assertEqual(self.client.get('/api/task-updates').json()['total'],0)
        task, first=self.submit(task,40,'anterior')
        task, latest=self.submit(task,60,'actual')
        self.assertEqual(self.client.post('/api/task-updates/'+first['id']+'/review',json={'revision':task['revision'],'status':'validada','note':'Versión anterior'}).status_code,409)
        task=self.review(task,latest)
        self.assertEqual(self.client.post('/api/task-updates/'+latest['id']+'/review',json={'revision':task['revision'],'status':'observada','note':'Repetida'}).status_code,409)
        self.assertEqual(self.client.post('/api/tasks/'+task['id']+'/advance',json=missing).status_code,409)

    def test_only_chief_permission_allows_team_and_review(self):
        hidden=self.task(title='Fuera del espacio')
        with self.factory() as db:
            role=db.scalar(select(m.Role).where(m.Role.name=='integrante'))
            permission=db.scalar(select(m.Permission).where(m.Permission.name=='tasks.validate'))
            db.add(m.RolePermission(role_id=role.id,permission_id=permission.id))
            db.commit()
        self.sign_in('member@example.invalid')
        self.assertEqual(self.client.get('/api/tasks?scope=team').status_code,403)
        self.assertEqual(self.client.post('/api/tasks/'+hidden['id']+'/close',json={'revision':1,'justification':'No tengo permiso de jefatura'}).status_code,403)
        self.sign_in()
        self.assertEqual(self.client.get('/api/tasks?scope=team').json()['total'],1)
        with self.factory() as db:
            role=db.scalar(select(m.Role).where(m.Role.name=='integrante'))
            permission=m.Permission(name='tasks.supervise');db.add(permission);db.flush()
            db.add(m.RolePermission(role_id=role.id,permission_id=permission.id));db.commit()
        self.sign_in('member@example.invalid')
        self.assertEqual(self.client.get('/api/tasks?scope=team').json()['total'],1)


if __name__ == '__main__':
    unittest.main()
