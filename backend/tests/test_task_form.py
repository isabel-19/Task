import unittest
from datetime import date,timedelta
from sqlalchemy import select,func
import test_api
from app import models as m


class TaskFormTest(unittest.TestCase):
    setUpClass=classmethod(test_api.APITest.setUpClass.__func__)
    tearDownClass=classmethod(test_api.APITest.tearDownClass.__func__)
    setUp=test_api.APITest.setUp
    tearDown=test_api.APITest.tearDown
    sign_in=test_api.APITest.sign_in
    create=test_api.APITest.create
    task=test_api.APITest.task

    def catalog(self):
        with self.factory() as db:
            db.add(m.ImportBatch(filename='ficticio.xlsx',sha256='a'*64,sheet='Temáticas y oficinas',backup_path='ficticio.xlsx',entity='task-catalogs',status='imported',mapping={},preview={
                'themes':[{'name':'Tema ficticio','axis_id':self.axis['id']}], 'offices':[{'name':'Oficina ficticia'}]}))
            db.commit()

    def minimal(self,**extra):
        return {'title':'Actividad ficticia','axis_id':self.axis['id'],'responsible_id':self.member.id,'due_date':str(date.today()+timedelta(days=5))}|extra

    def test_member_assigns_without_project_or_start_and_reuses_theme_group(self):
        self.sign_in('member@example.invalid')
        task=self.create('tasks',**self.minimal())
        self.assertEqual(task['axis_id'],self.axis['id'])
        self.assertEqual(task['start_date'],str(date.today()))
        self.assertEqual(task['status'],'pendiente')
        self.assertEqual(task['priority'],'media')
        other=self.create('tasks',**self.minimal(title='Segunda actividad',due_date=str(date.today()+timedelta(days=30))))
        self.assertEqual(other['project_id'],task['project_id'])
        with self.factory() as db:
            groups=list(db.scalars(select(m.Project).where(m.Project.group_key.is_not(None))))
            self.assertEqual(len(groups),1)
            self.assertEqual(groups[0].due_date,date.today()+timedelta(days=30))
        self.assertEqual(self.client.get('/api/tasks?scope=assigned').json()['total'],2)

    def test_offices_and_themes_come_from_catalog_and_unknown_office_is_rejected(self):
        self.catalog()
        choices=self.client.get('/api/lookups').json()
        self.assertEqual(choices['offices'],[{'value':'Oficina ficticia','label':'Oficina ficticia'}])
        self.assertEqual(choices['task-themes'][0]['value'],self.axis['id'])
        self.sign_in('member@example.invalid')
        good=self.create('tasks',**self.minimal(office='Oficina ficticia'))
        self.assertEqual(good['office'],'Oficina ficticia')
        for office in ['Otra oficina',{'name':'Oficina ficticia'}]:
            response=self.client.post('/api/tasks',json=self.minimal(title='No guardar',office=office))
            self.assertEqual(response.status_code,422,response.text)

    def test_edit_keeps_legacy_project_and_hidden_configuration(self):
        old=self.task(priority='alta',recurrence='mensual',description='Instrucción anterior')
        response=self.client.patch('/api/tasks/'+old['id'],json={'revision':old['revision'],'axis_id':self.axis['id'],'title':'Actividad editada','due_date':old['due_date'],'responsible_id':self.admin.id,'office':None})
        self.assertEqual(response.status_code,200,response.text)
        task=response.json()
        for field in ['project_id','start_date','priority','recurrence','description']:
            self.assertEqual(task[field],old[field])
        with self.factory() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(m.Project)),1)

    def test_invalid_submission_rolls_back_automatic_group(self):
        response=self.client.post('/api/tasks',json=self.minimal(status='cerrada'))
        self.assertEqual(response.status_code,422,response.text)
        with self.factory() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(m.Project).where(m.Project.group_key.is_not(None))),0)
            self.assertEqual(db.scalar(select(func.count()).select_from(m.Task)),0)

    def test_historical_deadline_gets_valid_start_and_group_key_cannot_be_spoofed(self):
        past=date.today()-timedelta(days=20)
        task=self.create('tasks',**self.minimal(due_date=str(past)))
        self.assertEqual(task['start_date'],str(past))
        response=self.client.patch('/api/projects/'+task['project_id'],json={'revision':1,'group_key':'arbitraria'})
        self.assertEqual(response.status_code,422,response.text)
