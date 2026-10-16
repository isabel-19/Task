import base64
import io
import hashlib
import shutil
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import select, func, create_engine
import test_api
from app import models as m
from app.config import settings
from app.evidence_storage import stored_path

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/a9sAAAAASUVORK5CYII=')
PDF = b'%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF'


def office_file(kind, xml, extra=None):
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', '<Types/>')
        archive.writestr('word/document.xml' if kind == 'docx' else 'xl/workbook.xml', xml)
        for name, content in (extra or {}).items():
            archive.writestr(name, content)
    return data.getvalue()


class EvidenceFilesTest(unittest.TestCase):
    setUpClass = classmethod(test_api.APITest.setUpClass.__func__)
    tearDownClass = classmethod(test_api.APITest.tearDownClass.__func__)
    sign_in = test_api.APITest.sign_in
    create = test_api.APITest.create
    task = test_api.APITest.task

    def setUp(self):
        test_api.APITest.setUp(self)
        self.folder = Path(__file__).resolve().parents[2] / '.local/test-evidence-files' / m.uid()
        self.folder.mkdir(parents=True)
        self.storage = patch.object(settings, 'evidence_storage_dir', str(self.folder))
        self.limit = patch.object(settings, 'evidence_max_upload_mb', 1)
        self.storage.start(); self.limit.start()

    def tearDown(self):
        self.storage.stop(); self.limit.stop()
        test_api.APITest.tearDown(self)
        root = Path(__file__).resolve().parents[2]
        assert self.folder.resolve().is_relative_to(root / '.local/test-evidence-files')
        shutil.rmtree(self.folder)

    def upload(self, task, name='informe.txt', data=b'Evidencia de prueba', **kwargs):
        return self.client.post('/api/tasks/'+task['id']+'/advance-file',
            data={'revision': str(task['revision']), 'progress': '60', 'comment': 'Mi entrega con archivo'},
            files={'file': (name, data, 'application/octet-stream')}, **kwargs)

    def test_member_upload_preview_download_chief_notification_and_review(self):
        task = self.task(responsible_id=self.member.id)
        with self.factory() as db:
            role = db.scalar(select(m.Role).where(m.Role.name == 'integrante'))
            grant = db.scalar(select(m.RolePermission).join(m.Permission).where(m.RolePermission.role_id == role.id, m.Permission.name == 'evidence.write'))
            db.delete(grant); db.commit()
        self.sign_in('member@example.invalid')
        response = self.upload(task, name='..\\informe ágil.txt', data='Entrega de revisión ágil'.encode())
        self.assertEqual(response.status_code, 200, response.text)
        task = response.json()
        file = task['latest_evidence_file']
        self.assertEqual(file['name'], 'informe ágil.txt')
        self.assertEqual(task['evidence_count'], 1)
        self.assertEqual(file['size'], len('Entrega de revisión ágil'.encode()))
        report = self.client.get('/api/task-updates?task_id='+task['id']).json()['items'][0]
        self.assertEqual(report['file'], file)
        self.assertFalse(report['can_review'])
        content = self.client.get(file['url'])
        self.assertEqual(content.content, 'Entrega de revisión ágil'.encode())
        self.assertIn('attachment', content.headers['content-disposition'])
        self.assertEqual(content.headers['x-content-type-options'], 'nosniff')
        preview = self.client.get(file['url']+'/preview')
        self.assertEqual(preview.status_code, 200, preview.text)
        self.assertEqual(preview.json()['text'], 'Entrega de revisión ágil')
        self.assertEqual(self.client.post('/api/evidence', json={'title':'Sin permiso global'}).status_code, 403)
        self.sign_in()
        self.assertEqual(self.client.get(file['url']).status_code, 200)
        self.assertTrue(any(item.get('id') == report['id'] for item in self.client.get('/api/alerts').json()))
        review = self.client.post('/api/task-updates/'+report['id']+'/review', json={'revision': task['revision'], 'status':'validada', 'note':'Archivo leído y revisado'})
        self.assertEqual(review.status_code, 200, review.text)
        with self.factory() as db:
            stored = db.get(m.EvidenceFile, file['id'])
            self.assertEqual(stored.sha256, hashlib.sha256(content.content).hexdigest())
            self.assertTrue(stored_path(stored.storage_key).is_file())

    def test_file_content_and_preview_follow_task_permissions_and_session(self):
        task = self.task()
        response = self.upload(task)
        self.assertEqual(response.status_code, 200, response.text)
        file = response.json()['latest_evidence_file']
        self.sign_in('member@example.invalid')
        for suffix in ('', '?download=true', '/preview'):
            self.assertEqual(self.client.get(file['url']+suffix).status_code, 403)
        self.client.cookies.clear()
        self.assertEqual(self.client.get(file['url']).status_code, 401)
        self.sign_in('reader@example.invalid')
        self.assertEqual(self.client.get(file['url']).status_code, 403)
        with self.factory() as db:
            role = db.scalar(select(m.Role).where(m.Role.name == 'consulta_auditoria'))
            permission = m.Permission(name='tasks.team_read'); db.add(permission); db.flush()
            db.add(m.RolePermission(role_id=role.id, permission_id=permission.id)); db.commit()
        self.assertEqual(self.client.get(file['url']).status_code, 200)

    def test_pdf_images_word_excel_and_csv_previews(self):
        docx = office_file('docx', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Informe aprobado</w:t></w:r></w:p></w:body></w:document>')
        xlsx = office_file('xlsx', '<workbook/>', {'xl/worksheets/sheet1.xml': '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Avance</t></is></c><c r="C1"><v>60</v></c></row></sheetData></worksheet>'})
        for name, data, expected in [('evidencia.pdf', PDF, None), ('captura.png', PNG, None), ('informe.docx', docx, 'Informe aprobado'), ('avance.xlsx', xlsx, [['Avance', '', '60']]), ('detalle.csv', b'Persona;Avance\nElena;60', [['Persona','Avance'],['Elena','60']])]:
            with self.subTest(name=name):
                task = self.task(title=name)
                response = self.upload(task, name, data)
                self.assertEqual(response.status_code, 200, response.text)
                file = response.json()['latest_evidence_file']
                served = self.client.get(file['url'])
                self.assertEqual(served.content, data)
                if expected is None:
                    self.assertIn('inline', served.headers['content-disposition'])
                else:
                    preview = self.client.get(file['url']+'/preview')
                    self.assertEqual(preview.status_code, 200, preview.text)
                    actual = preview.json().get('text') if isinstance(expected, str) else preview.json()['sheets'][0]['rows']
                    self.assertEqual(actual, expected)
                self.assertIn('attachment', self.client.get(file['url']+'?download=true').headers['content-disposition'])

    def test_office_previews_keep_headings_tables_and_real_sheet_names(self):
        from app.evidence_storage import document_preview_bytes
        word = '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' \
            '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Plan 2026</w:t></w:r></w:p>' \
            '<w:p><w:r><w:t>Resumen del avance</w:t></w:r></w:p>' \
            '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Meta</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Logro</w:t></w:r></w:p></w:tc></w:tr>' \
            '<w:tr><w:tc><w:p><w:r><w:t>60</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>58</w:t></w:r></w:p></w:tc></w:tr></w:tbl>' \
            '</w:body></w:document>'
        preview = document_preview_bytes(office_file('docx', word), 'plan.docx')
        self.assertEqual(preview['blocks'][0], {'kind': 'heading', 'level': 1, 'text': 'Plan 2026'})
        self.assertEqual(preview['blocks'][1], {'kind': 'paragraph', 'text': 'Resumen del avance'})
        self.assertEqual(preview['blocks'][2], {'kind': 'table', 'rows': [['Meta', 'Logro'], ['60', '58']], 'truncated': False})
        self.assertIn('Plan 2026', preview['text'])
        sheet = lambda n: f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>{n}</t></is></c></row></sheetData></worksheet>'
        workbook = '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>' \
            '<sheet name="Seguimiento" sheetId="1" r:id="rId2"/><sheet name="Metas" sheetId="2" r:id="rId1"/></sheets></workbook>'
        rels = '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' \
            '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Target="/xl/worksheets/sheet2.xml"/></Relationships>'
        xlsx = office_file('xlsx', workbook, {'xl/_rels/workbook.xml.rels': rels,
                                              'xl/worksheets/sheet1.xml': sheet('uno'), 'xl/worksheets/sheet2.xml': sheet('dos')})
        preview = document_preview_bytes(xlsx, 'libro.xlsx')
        self.assertEqual([s['name'] for s in preview['sheets']], ['Seguimiento', 'Metas'])
        self.assertEqual(preview['sheets'][0]['rows'], [['dos']])
        self.assertEqual(preview['sheets'][1]['rows'], [['uno']])

    def test_rejected_uploads_do_not_create_files_or_reports(self):
        task = self.task()
        macro = office_file('docx', '<document/>', {'word/vbaProject.bin': b'fake macro'})
        for name, data in [('ejecutar.exe', b'MZ'), ('imagen.png', b'<html>no</html>'), ('vacio.txt', b''), ('informe.docx', b'no es ZIP'), ('macro.docx', macro), ('grande.txt', b'a'*(1024*1024+1))]:
            with self.subTest(name=name):
                result = self.upload(task, name, data)
                self.assertIn(result.status_code, (413, 422), result.text)
                self.assertEqual(list(self.folder.iterdir()), [])
        with self.factory() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(m.TaskUpdate)), 0)
            self.assertEqual(db.scalar(select(func.count()).select_from(m.EvidenceFile)), 0)

    def test_upload_requires_csrf_membership_and_current_revision(self):
        task = self.task()
        self.assertEqual(self.upload(task, headers={'X-CSRF-Token':''}).status_code, 403)
        self.sign_in('member@example.invalid')
        self.assertEqual(self.upload(task).status_code, 403)
        self.sign_in()
        changed = self.client.patch('/api/tasks/'+task['id'], json={'revision': task['revision'], 'description':'Cambio concurrente'}).json()
        self.assertEqual(self.upload(task).status_code, 409)
        self.assertEqual(self.upload(changed, headers={'Content-Length':str(2*1024*1024)}).status_code, 413)
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_failed_database_write_cleans_uploaded_file(self):
        task = self.task()
        with patch('app.task_routes.record_advance', side_effect=RuntimeError('Fallo ficticio de base')):
            with self.assertRaises(RuntimeError):
                self.upload(task)
        self.assertEqual(list(self.folder.iterdir()), [])
        with self.factory() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(m.EvidenceFile)), 0)

    def test_streamed_body_without_length_is_bounded(self):
        task = self.task()
        body = (f'--ogc\r\nContent-Disposition: form-data; name="revision"\r\n\r\n{task["revision"]}\r\n'
                '--ogc\r\nContent-Disposition: form-data; name="progress"\r\n\r\n50\r\n'
                '--ogc\r\nContent-Disposition: form-data; name="comment"\r\n\r\nEvidencia grande\r\n'
                '--ogc\r\nContent-Disposition: form-data; name="file"; filename="informe.txt"\r\nContent-Type: text/plain\r\n\r\n').encode()
        chunks = iter([body, b'a' * (2 * 1024 * 1024), b'\r\n--ogc--\r\n'])
        response = self.client.post('/api/tasks/'+task['id']+'/advance-file', content=chunks,
                                    headers={'Content-Type': 'multipart/form-data; boundary=ogc'})
        self.assertEqual(response.status_code, 413, response.text)
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_incomplete_attachment_does_not_prevent_reading_task_and_returns_clear_error(self):
        task = self.task()
        response = self.upload(task)
        file = response.json()['latest_evidence_file']
        with self.factory() as db:
            row = db.get(m.EvidenceFile, file['id'])
            stored_path(row.storage_key).write_bytes(b'')
        self.assertEqual(self.client.get('/api/tasks/'+task['id']).status_code, 200)
        response = self.client.get(file['url'])
        self.assertEqual(response.status_code, 404)
        self.assertIn('no está disponible', response.json()['detail'])

    def test_installation_can_disable_new_uploads_without_affecting_saved_files(self):
        task = self.task()
        response = self.upload(task)
        self.assertEqual(response.status_code, 200, response.text)
        file = response.json()['latest_evidence_file']
        with patch.object(settings, 'evidence_uploads_enabled', False):
            self.assertEqual(self.upload(response.json()).status_code, 503)
            self.assertEqual(self.client.get(file['url']).status_code, 200)
            self.assertFalse(self.client.get('/api/meta').json()['tasks']['evidence_upload']['enabled'])


class EvidenceFileMigrationTest(unittest.TestCase):
    def test_additive_migration_is_repeatable_and_does_not_touch_existing_rows(self):
        engine = create_engine('sqlite://')
        root = Path(__file__).resolve().parents[2]
        with engine.begin() as connection:
            for name in ['001_initial_sqlite.sql', '002_task_collaboration_sqlite.sql', '003_task_form_sqlite.sql', '004_document_registry_sqlite.sql', '005_document_axis_sqlite.sql', '006_document_workflow_sqlite.sql', '007_chief_administration_sqlite.sql']:
                for statement in (root / 'database/migrations' / name).read_text(encoding='utf-8').split(';'):
                    if statement.strip(): connection.exec_driver_sql(statement)
            connection.exec_driver_sql("INSERT INTO users(id,name,email,password_hash,active,department,created_at,updated_at,revision) VALUES('test','Prueba','prueba@example.invalid','ficticio',1,'OGC',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,1)")
            before = connection.exec_driver_sql('SELECT * FROM users').all()
            for _ in range(2):
                for statement in (root / 'database/migrations/008_evidence_files_sqlite.sql').read_text(encoding='utf-8').split(';'):
                    if statement.strip(): connection.exec_driver_sql(statement)
            self.assertEqual(connection.exec_driver_sql('SELECT * FROM users').all(), before)
            self.assertEqual(connection.exec_driver_sql('SELECT count(*) FROM evidence_files').scalar(), 0)
            self.assertEqual(connection.exec_driver_sql('PRAGMA foreign_key_check').all(), [])
        engine.dispose()
