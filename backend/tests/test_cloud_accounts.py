import base64
import hashlib
import json
import shutil
import time
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse, parse_qs
import httpx
from authlib.integrations.httpx_client import OAuth2Client
from cryptography.fernet import Fernet
from sqlalchemy import select, func
import test_api
from app import models as m
from app.config import settings
from app import cloud_accounts as cloud
from app import cloud_files

PDF = b'%PDF-1.4\nDocumento ficticio\n%%EOF'


class CloudAccountsTest(unittest.TestCase):
    setUpClass = classmethod(test_api.APITest.setUpClass.__func__)
    tearDownClass = classmethod(test_api.APITest.tearDownClass.__func__)
    sign_in = test_api.APITest.sign_in
    create = test_api.APITest.create
    task = test_api.APITest.task

    def setUp(self):
        test_api.APITest.setUp(self)
        self.folder = Path(__file__).resolve().parents[2] / '.local/test-cloud-files' / m.uid()
        self.folder.mkdir(parents=True)
        self.patches = []
        config = dict(cloud_token_key=Fernet.generate_key().decode(), cloud_public_api_url='https://api.example.invalid/api',
                      cloud_frontend_url='https://frontend.example.invalid', frontend_origins='https://frontend.example.invalid',
                      google_client_id='google-test-client', google_client_secret='google-test-secret',
                      google_picker_api_key='picker-test-key', google_project_number='123456',
                      microsoft_client_id='ms-test-client', microsoft_client_secret='ms-test-secret',
                      microsoft_tenant='common', evidence_storage_dir=str(self.folder))
        for name, value in config.items():
            item = patch.object(settings, name, value); item.start(); self.patches.append(item)
        self.requests = []
        self.transport = httpx.MockTransport(self.upstream)
        item = patch.object(cloud, 'oauth_client', self.oauth_client); item.start(); self.patches.append(item)
        item = patch.object(cloud_files, 'http_client', lambda: httpx.Client(transport=self.transport)); item.start(); self.patches.append(item)

    def tearDown(self):
        for item in reversed(self.patches): item.stop()
        test_api.APITest.tearDown(self)
        assert self.folder.resolve().is_relative_to(Path(__file__).resolve().parents[2] / '.local/test-cloud-files')
        shutil.rmtree(self.folder)

    def oauth_client(self, provider, token=None, db=None):
        config = cloud.provider_config(provider, db)
        return OAuth2Client(config['client_id'], config['client_secret'], scope=config['scope'],
                            redirect_uri=cloud.callback_url(provider, db), token=token, code_challenge_method='S256',
                            token_endpoint_auth_method='client_secret_post', transport=self.transport)

    def upstream(self, request):
        self.requests.append(request)
        host, path = request.url.host, request.url.path
        if path.endswith('/token'):
            provider = 'google' if host == 'oauth2.googleapis.com' else 'microsoft'
            return httpx.Response(200, json={'access_token': provider+'-access-fixture', 'refresh_token': provider+'-refresh-fixture',
                                            'token_type':'Bearer', 'expires_in':3600, 'scope': cloud.provider_config(provider)['scope']})
        if host == 'openidconnect.googleapis.com':
            return httpx.Response(200, json={'sub':'google-subject-fixture', 'email':'google@example.invalid', 'email_verified':True})
        if path == '/v1.0/me':
            return httpx.Response(200, json={'id':'ms-subject-fixture', 'mail':'outlook@example.invalid'})
        if path.endswith('/children'):
            return httpx.Response(200, json={'value':[
                {'id':'folder-1', 'name':'Informes', 'folder':{}, 'webUrl':'https://onedrive.live.com/folder'},
                {'id':'file-1', 'name':'informe.txt', 'size':18, 'file':{}, 'webUrl':'https://onedrive.live.com/file'},
            ]})
        if path.endswith('/content'):
            return httpx.Response(302, headers={'location':'https://files.1drv.com/download-fixture'})
        if host == 'files.1drv.com':
            self.assertNotIn('authorization', request.headers)
            return httpx.Response(200, content=b'Informe OneDrive')
        if host == 'graph.microsoft.com' and path.endswith('/file-1'):
            return httpx.Response(200, json={'id':'file-1','name':'informe.txt','size':16,'file':{},'webUrl':'https://onedrive.live.com/file'})
        if path.endswith('/export'):
            return httpx.Response(200, content=PDF)
        if host == 'www.googleapis.com' and path.endswith('/doc-1'):
            return httpx.Response(200, json={'id':'doc-1','name':'Informe de Google','mimeType':'application/vnd.google-apps.document','webViewLink':'https://docs.google.com/document/d/doc-1/edit','capabilities':{'canDownload':True}})
        raise AssertionError('Solicitud de prueba no prevista: '+str(request.url))

    def start(self, provider):
        result = self.client.post('/api/cloud/'+provider+'/connect')
        self.assertEqual(result.status_code, 200, result.text)
        return parse_qs(urlparse(result.json()['authorization_url']).query)

    def connect(self, provider):
        query = self.start(provider)
        response = self.client.get('/api/cloud/'+provider+'/callback', params={'state':query['state'][0], 'code':'authorization-fixture'}, follow_redirects=False)
        self.assertEqual(response.status_code, 303, response.text)
        return query

    def test_oauth_pkce_single_use_state_encryption_and_public_status(self):
        query = self.start('google')
        self.assertNotIn('client_secret', query)
        self.assertEqual(query['code_challenge_method'], ['S256'])
        with self.factory() as db:
            state = db.scalar(select(m.CloudOAuthState))
            verifier = cloud.decrypt(state.verifier_ciphertext)
            expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
            self.assertEqual(query['code_challenge'][0], expected)
        response = self.client.get('/api/cloud/google/callback', params={'state':query['state'][0], 'code':'authorization-fixture'}, follow_redirects=False)
        self.assertEqual(response.status_code, 303, response.text)
        self.assertEqual(response.headers['location'], 'https://frontend.example.invalid/cuentas?provider=google&status=connected')
        self.assertEqual(self.client.get('/api/cloud/google/callback', params={'state':query['state'][0], 'code':'replay'}).status_code, 400)
        with self.factory() as db:
            account = db.scalar(select(m.CloudAccount))
            self.assertNotIn('google-access-fixture', account.token_ciphertext)
            self.assertEqual(cloud.decrypt(account.token_ciphertext)['refresh_token'], 'google-refresh-fixture')
            audit = '\n'.join(json.dumps(row.after) for row in db.scalars(select(m.Audit)))
            self.assertNotIn('google-access-fixture', audit)
            self.assertNotIn('google-refresh-fixture', audit)
        status = self.client.get('/api/cloud/accounts').json()
        self.assertTrue(next(row['connected'] for row in status['items'] if row['provider']=='google'))
        self.assertNotIn('access_token', json.dumps(status))
        token_request = next(request for request in self.requests if request.url.path.endswith('/token'))
        self.assertEqual(parse_qs(token_request.content.decode())['code_verifier'], [verifier])

    def test_state_belongs_to_initiating_user_session_and_provider(self):
        query = self.start('google')
        self.assertEqual(self.client.get('/api/cloud/microsoft/callback', params={'state':query['state'][0],'code':'fixture'}).status_code, 400)
        self.sign_in('member@example.invalid')
        self.assertEqual(self.client.get('/api/cloud/google/callback', params={'state':query['state'][0],'code':'fixture'}).status_code, 400)
        self.sign_in()
        self.assertEqual(self.client.get('/api/cloud/google/callback', params={'state':query['state'][0],'code':'fixture'}).status_code, 400)
        self.assertFalse(self.requests)

    def test_cancelled_and_expired_authorizations_do_not_connect(self):
        query = self.start('google')
        cancelled = self.client.get('/api/cloud/google/callback', params={'state':query['state'][0],'error':'access_denied'}, follow_redirects=False)
        self.assertIn('status=cancelled', cancelled.headers['location'])
        query = self.start('microsoft')
        with self.factory() as db:
            state = db.scalar(select(m.CloudOAuthState)); state.expires_at=m.now()-timedelta(seconds=1); db.commit()
        self.assertEqual(self.client.get('/api/cloud/microsoft/callback', params={'state':query['state'][0],'code':'fixture'}).status_code, 400)
        with self.factory() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(m.CloudAccount)), 0)

    def test_connections_are_private_and_disconnect_requires_csrf(self):
        self.connect('microsoft')
        self.assertEqual(self.client.post('/api/cloud/microsoft/disconnect', headers={'X-CSRF-Token':''}).status_code, 403)
        self.sign_in('member@example.invalid')
        self.assertFalse(any(row['connected'] for row in self.client.get('/api/cloud/accounts').json()['items']))
        self.assertEqual(self.client.get('/api/cloud/microsoft/files').status_code, 409)
        self.client.post('/api/cloud/microsoft/disconnect')
        self.sign_in()
        self.assertTrue(any(row['connected'] for row in self.client.get('/api/cloud/accounts').json()['items']))

    def test_expired_access_token_refreshes_without_exposing_refresh_token(self):
        self.connect('microsoft')
        with self.factory() as db:
            row=db.scalar(select(m.CloudAccount)); token=cloud.decrypt(row.token_ciphertext); token['expires_at']=time.time()-10; row.token_ciphertext=cloud.encrypt(token); db.commit()
        response = self.client.get('/api/cloud/microsoft/files')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()['items']), 2)
        self.assertTrue(any(b'grant_type=refresh_token' in request.content for request in self.requests if request.method=='POST'))

    def test_cloud_google_doc_becomes_private_pdf_evidence_and_notifies_chief(self):
        task = self.task(responsible_id=self.member.id)
        self.sign_in('member@example.invalid'); self.connect('google')
        response = self.client.post('/api/tasks/'+task['id']+'/advance-cloud', json={'revision':task['revision'],'progress':70,'comment':'Documento autorizado de mi cuenta','provider':'google','item_id':'doc-1'})
        self.assertEqual(response.status_code, 200, response.text)
        file=response.json()['latest_evidence_file']
        self.assertEqual(file['name'], 'Informe de Google.pdf')
        self.assertEqual(file['source']['provider'], 'google')
        self.assertEqual(self.client.get(file['url']).content, PDF)
        self.client.post('/api/cloud/google/disconnect')
        self.assertEqual(self.client.get(file['url']).status_code, 200)
        self.sign_in()
        self.assertEqual(self.client.get(file['url']).content, PDF)
        self.assertTrue(any(row.get('task_id')==task['id'] and row.get('kind')=='task_review' for row in self.client.get('/api/alerts').json()))

    def test_microsoft_file_download_strips_bearer_on_download_redirect(self):
        task=self.task(); self.connect('microsoft')
        response=self.client.post('/api/tasks/'+task['id']+'/advance-cloud', json={'revision':task['revision'],'progress':60,'comment':'Archivo OneDrive','provider':'microsoft','item_id':'file-1'})
        self.assertEqual(response.status_code, 200, response.text)
        file=response.json()['latest_evidence_file']
        self.assertEqual(self.client.get(file['url']+'/preview').json()['text'], 'Informe OneDrive')

    def test_unconfigured_provider_and_unassigned_task_cannot_download(self):
        task=self.task()
        self.sign_in('member@example.invalid')
        response=self.client.post('/api/tasks/'+task['id']+'/advance-cloud', json={'revision':1,'progress':50,'comment':'No pertenece','provider':'google','item_id':'doc-1'})
        self.assertEqual(response.status_code, 403)
        with patch.object(settings, 'google_client_secret', ''):
            self.assertEqual(self.client.post('/api/cloud/google/connect').status_code, 503)
            status=self.client.get('/api/cloud/accounts').json()['items']
            self.assertFalse(next(row['configured'] for row in status if row['provider']=='google'))
        self.assertFalse(self.requests)

    def test_remote_path_injection_and_unsigned_cursor_are_rejected(self):
        self.connect('microsoft')
        self.assertEqual(self.client.get('/api/cloud/microsoft/files?folder=../users').status_code, 422)
        self.assertEqual(self.client.get('/api/cloud/microsoft/files?cursor=https://internal.invalid').status_code, 409)

    def test_contributor_previews_selected_google_doc_privately_without_creating_evidence(self):
        self.sign_in('member@example.invalid')
        self.connect('google')
        response = self.client.post('/api/cloud/google/preview', json={'item_id': 'doc-1'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.content, PDF)
        self.assertEqual(response.headers['content-type'], 'application/pdf')
        self.assertEqual(response.headers['cache-control'], 'no-store')
        metadata_request = next(request for request in self.requests if request.url.path.endswith('/doc-1'))
        self.assertEqual(metadata_request.url.params['supportsAllDrives'], 'true')
        with self.factory() as db:
            for model in (m.EvidenceFile, m.Evidence, m.TaskUpdate):
                self.assertEqual(db.scalar(select(func.count()).select_from(model)), 0)
        self.assertEqual(list(self.folder.iterdir()), [])
        count = len(self.requests)
        self.sign_in()
        self.assertEqual(self.client.post('/api/cloud/google/preview', json={'item_id': 'doc-1'}).status_code, 409)
        self.assertEqual(len(self.requests), count)
        self.sign_in('reader@example.invalid')
        self.assertEqual(self.client.post('/api/cloud/google/preview', json={'item_id': 'doc-1'}).status_code, 403)

    def test_shared_google_text_preview_and_owner_copy_restriction(self):
        self.connect('google')
        def shared(request):
            self.assertEqual(request.url.params.get('supportsAllDrives'), 'true')
            if request.url.params.get('alt') == 'media':
                return httpx.Response(200, content=b'Contenido compartido conmigo')
            return httpx.Response(200, json={'id': 'shared-1', 'name': 'Compartido.txt', 'mimeType': 'text/plain',
                'owners': [{'emailAddress': 'otra-persona@example.invalid'}], 'capabilities': {'canDownload': True},
                'webViewLink': 'https://drive.google.com/file/d/shared-1/view'})
        with patch.object(cloud_files, 'http_client', lambda: httpx.Client(transport=httpx.MockTransport(shared))):
            response = self.client.post('/api/cloud/google/preview', json={'item_id': 'shared-1'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['text'], 'Contenido compartido conmigo')
        def blocked(request):
            self.assertNotIn('alt', request.url.params)
            return httpx.Response(200, json={'id': 'shared-1', 'name': 'Restringido.txt', 'mimeType': 'text/plain', 'capabilities': {'canDownload': False}})
        with patch.object(cloud_files, 'http_client', lambda: httpx.Client(transport=httpx.MockTransport(blocked))):
            response = self.client.post('/api/cloud/google/preview', json={'item_id': 'shared-1'})
        self.assertEqual(response.status_code, 403)
        self.assertIn('propietario', response.text)

    def test_provider_connection_failure_returns_to_accounts_without_credentials_in_logs(self):
        query = self.start('google')
        with patch.object(cloud, 'oauth_client') as client:
            client.return_value.__enter__.return_value.fetch_token.side_effect = httpx.ConnectError('sensitive-provider-details')
            with self.assertLogs('app.cloud_accounts', level='WARNING') as log:
                response = self.client.get('/api/cloud/google/callback', params={'state': query['state'][0], 'code': 'secret-authorization-fixture'}, follow_redirects=False)
        self.assertEqual(response.status_code, 303, response.text)
        self.assertEqual(response.headers['location'], 'https://frontend.example.invalid/cuentas?provider=google&status=failed')
        self.assertNotIn('sensitive-provider-details', str(log.output))
        self.assertNotIn('secret-authorization-fixture', str(log.output))

    def test_configuration_is_central_encrypted_and_admin_only(self):
        initial = self.client.get('/api/cloud/configuration').json()
        self.assertEqual(initial['revision'], 0)
        self.assertNotIn('google_client_secret', initial['fields'])
        body = {'revision': 0, 'google_client_id': 'central-google-client',
                'google_client_secret': 'central-secret-fixture', 'google_picker_api_key': 'central-picker-fixture'}
        self.assertEqual(self.client.post('/api/cloud/configuration', json=body, headers={'X-CSRF-Token': ''}).status_code, 403)
        response = self.client.post('/api/cloud/configuration', json=body)
        self.assertEqual(response.status_code, 200, response.text)
        public = response.json()
        self.assertTrue(public['providers']['google']['configured'])
        self.assertNotIn('central-secret-fixture', response.text)
        self.assertNotIn('central-picker-fixture', response.text)
        self.assertTrue(public['saved_secrets']['google_client_secret'])
        self.assertEqual(self.client.post('/api/cloud/configuration', json=body).status_code, 409)
        response = self.client.post('/api/cloud/configuration', json={'revision': 1, 'google_client_secret': ''})
        self.assertEqual(response.status_code, 200, response.text)
        with self.factory() as db:
            stored = db.get(m.CloudConfiguration, 'application')
            self.assertNotIn('central-secret-fixture', stored.settings_ciphertext)
            self.assertEqual(cloud.decrypt(stored.settings_ciphertext)['google_client_secret'], 'central-secret-fixture')
            audit = json.dumps([row.after for row in db.scalars(select(m.Audit))])
            self.assertNotIn('central-secret-fixture', audit)
            self.assertNotIn('central-picker-fixture', audit)
        self.sign_in('member@example.invalid')
        self.assertEqual(self.client.get('/api/cloud/configuration').status_code, 403)
        self.assertEqual(self.client.post('/api/cloud/configuration', json={'revision': 2}).status_code, 403)
        self.assertEqual(self.start('google')['client_id'], ['central-google-client'])
        # A regular task contributor authorizes a personal account using the shared registration.
        self.connect('google')
        self.assertTrue(any(row['connected'] for row in self.client.get('/api/cloud/accounts').json()['items']))
        self.sign_in()
        self.assertFalse(any(row['connected'] for row in self.client.get('/api/cloud/accounts').json()['items']))
        self.sign_in('reader@example.invalid')
        self.assertEqual(self.client.post('/api/cloud/google/connect').status_code, 403)

    def test_configuration_validation_and_application_changes_require_reconnection(self):
        self.connect('google')
        query = self.start('google')
        for changes in ({'cloud_frontend_url': 'https://untrusted.invalid'},
                        {'cloud_public_api_url': 'http://private.invalid/api'},
                        {'cloud_public_api_url': 'https://['},
                        {'cloud_public_api_url': 'https://api.example.invalid:invalid/api'},
                        {'microsoft_tenant': '../../other'}, {'google_project_number': 'abc'}):
            response = self.client.post('/api/cloud/configuration', json={'revision': 0, **changes})
            self.assertEqual(response.status_code, 422, response.text)
        response = self.client.post('/api/cloud/configuration', json={'revision': 0, 'google_client_id': 'changed-app'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertFalse(any(row['connected'] for row in self.client.get('/api/cloud/accounts').json()['items']))
        self.assertEqual(self.client.get('/api/cloud/google/callback', params={'state': query['state'][0], 'code': 'old-app'}).status_code, 400)
        with self.factory() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(m.CloudOAuthState)), 0)
