import io
import json
import shutil
from contextlib import contextmanager
import unittest
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape
from sqlalchemy import select, func
import test_api
from app import models as m
from app.participant_import import parse_participants, register_participants

WORKSPACE=Path(__file__).resolve().parents[2]
TEST_STORAGE=WORKSPACE/'.local/test-participant-import'
assert TEST_STORAGE.resolve().is_relative_to(WORKSPACE)
TEST_STORAGE.mkdir(parents=True,exist_ok=True)


@contextmanager
def test_folder():
    folder=TEST_STORAGE/m.uid()
    folder.mkdir()
    try:
        yield folder
    finally:
        if not folder.resolve().is_relative_to(TEST_STORAGE.resolve()):
            raise RuntimeError('El directorio de pruebas salió del espacio permitido.')
        shutil.rmtree(folder)


def source_book(rows):
    result=io.BytesIO()
    cells=[]
    for number,values in rows:
        cells.append('<row r="'+str(number)+'">'+''.join('<c r="'+col+str(number)+'" t="inlineStr"><is><t>'+escape(value)+'</t></is></c>' for col,value in values.items())+'</row>')
    with zipfile.ZipFile(result,'w') as archive:
        archive.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="OCTUBRE" sheetId="1" r:id="r1"/></sheets></workbook>')
        archive.writestr('xl/_rels/workbook.xml.rels','<Relationships><Relationship Id="r1" Target="worksheets/sheet1.xml"/></Relationships>')
        archive.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+''.join(cells)+'</sheetData></worksheet>')
    return result.getvalue()


class ParticipantImportTest(unittest.TestCase):
    setUpClass=classmethod(test_api.APITest.setUpClass.__func__)
    tearDownClass=classmethod(test_api.APITest.tearDownClass.__func__)
    setUp=test_api.APITest.setUp
    tearDown=test_api.APITest.tearDown
    sign_in=test_api.APITest.sign_in
    create=test_api.APITest.create

    def fixture(self):
        return source_book([(2,{'C':'Participantes','F':'Responsable de la actividad'}),
                            (4,{'C':'Prueba Alfa / Prueba Beta','F':'Prueba Alfa'}),
                            (5,{'C':'PRUEBA ÁLFA','F':'Todo el equipo'}),
                            (6,{'C':'Prueba Gama y Prueba Gamma','F':'AVANZA'})])

    def test_exact_dedup_group_splitting_provenance_and_uncertain_variants(self):
        manifest=parse_participants('ficticio.xlsx',self.fixture())
        people={p['key']:p for p in manifest['people']}
        self.assertEqual(len(people),4)
        self.assertEqual(people['prueba alfa']['name'],'Prueba Álfa')
        self.assertEqual({r['cell'] for r in people['prueba alfa']['references']},{'C4','F4','C5'})
        self.assertIn('prueba gamma',people['prueba gama']['possible_variants'])
        self.assertEqual(len(manifest['ignored']),2)
        self.assertNotIn('todo el equipo',people)

    def test_register_login_roles_selectors_provenance_and_no_password_leak(self):
        data=self.fixture();manifest=parse_participants('ficticio.xlsx',data)
        with test_folder() as folder:
            access=Path(folder)/'private-access.json'
            with self.factory() as db:
                result=register_participants(db,self.admin,manifest,data,Path(folder)/'imports',access)
                self.assertEqual(result['created'],4)
                self.assertEqual((Path(folder)/'imports'/(manifest['sha256']+'-participants.xlsx')).read_bytes(),data)
                before=db.scalar(select(func.count()).select_from(m.User))
                repeat=register_participants(db,self.admin,parse_participants('ficticio.xlsx',data),data,Path(folder)/'imports',access)
                self.assertTrue(repeat['already_imported'])
                self.assertEqual(db.scalar(select(func.count()).select_from(m.User)),before)
                batch=db.get(m.ImportBatch,result['batch_id'])
                self.assertEqual(batch.preview['people'][0]['references'][0]['sheet'],'OCTUBRE')
                audits=list(db.scalars(select(m.Audit).where(m.Audit.action=='import_participant')))
                self.assertNotIn('password_hash',json.dumps([a.after for a in audits]))
            account=next(iter(json.loads(access.read_text(encoding='utf-8'))['accounts'].values()))
            self.client.cookies.clear()
            login=self.client.post('/api/auth/login',json={'email':account['identifier'],'password':account['password']})
            self.assertEqual(login.status_code,200,login.text)
            self.assertEqual(login.json()['roles'],['integrante'])
            self.assertTrue(login.json()['has_real_participants'])
            self.assertNotIn('tasks.supervise',login.json()['permissions'])
            self.assertEqual(self.client.get('/api/tasks').json()['total'],0)
            names=[p['label'] for p in self.client.get('/api/lookups').json()['task-members']]
            self.assertIn(account['name'],names)
            directory=self.client.get('/api/participants')
            self.assertEqual(directory.status_code,200,directory.text)
            self.assertEqual(directory.json()['imported_count'],4)
            self.assertNotIn(account['password'],directory.text)
            self.assertEqual(self.client.get('/api/users').status_code,403)

    def test_changed_source_reuses_accounts_and_does_not_change_passwords(self):
        first=self.fixture()
        second=source_book([(2,{'C':'Participantes'}),(4,{'C':'Prueba Alfa / Prueba Beta'}),(5,{'C':'Prueba Delta'})])
        with test_folder() as folder:
            path=Path(folder)/'private-access.json'
            with self.factory() as db:
                register_participants(db,self.admin,parse_participants('ficticio.xlsx',first),first,folder,path)
                passwords={u.id:u.password_hash for u in db.scalars(select(m.User))}
                result=register_participants(db,self.admin,parse_participants('otra-version.xlsx',second),second,folder,path)
                self.assertEqual((result['created'],result['reused']),(1,2))
                self.assertTrue(all(db.get(m.User,identifier).password_hash==value for identifier,value in passwords.items()))
                self.assertEqual(len(json.loads(path.read_text(encoding='utf-8'))['accounts']),5)

    def test_existing_user_keeps_roles_and_password_and_hidden_task_counts_stay_private(self):
        data=source_book([(2,{'C':'Participantes'}),(4,{'C':self.member.name})])
        with test_folder() as folder:
            with self.factory() as db:
                result=register_participants(db,self.admin,parse_participants('ficticio.xlsx',data),data,folder,Path(folder)/'access.json')
                self.assertEqual((result['created'],result['reused']),(0,1))
            self.sign_in('member@example.invalid')
            response=self.client.get('/api/participants')
            self.assertEqual(response.status_code,200,response.text)
            self.assertEqual(response.json()['imported_count'],1)
            for person in response.json()['items']:
                if person['id'] != self.member.id:
                    self.assertIsNone(person['identifier'])
