"""Provider-contract tests: private storage survives independent HTTP clients."""
import unittest
from unittest.mock import patch
from pydantic import SecretStr
import httpx
import test_api
from app.config import settings
from app.evidence_objects import remote_config


class RemoteEvidenceTest(unittest.TestCase):
    setUpClass = classmethod(test_api.APITest.setUpClass.__func__)
    tearDownClass = classmethod(test_api.APITest.tearDownClass.__func__)
    sign_in = test_api.APITest.sign_in
    create = test_api.APITest.create
    task = test_api.APITest.task

    def setUp(self):
        test_api.APITest.setUp(self)
        self.objects, self.requests = {}, []
        self.public = False
        self.redirect_upload = False
        self.patches = []
        for name, value in dict(evidence_storage_backend='supabase', supabase_url='https://project-test.supabase.co',
                                supabase_storage_bucket='roadmap-evidence', supabase_service_key=SecretStr('sb_secret_ficticio')).items():
            self.patches.append(patch.object(settings, name, value))
        sync_client, async_client = httpx.Client, httpx.AsyncClient
        self.patches += [
            patch('app.evidence_objects.httpx.Client', side_effect=lambda **kw: sync_client(transport=httpx.MockTransport(self.provider), **kw)),
            patch('app.evidence_objects.httpx.AsyncClient', side_effect=lambda **kw: async_client(transport=httpx.MockTransport(self.provider), **kw)),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        test_api.APITest.tearDown(self)

    def provider(self, request):
        self.requests.append((request.method, request.url.path))
        self.assertEqual(request.url.host, 'project-test.supabase.co')
        self.assertEqual(request.headers['apikey'], 'sb_secret_ficticio')
        self.assertNotIn('authorization', request.headers)
        if '/bucket/' in request.url.path:
            return httpx.Response(200, json={'public': self.public})
        key = request.url.path.rsplit('/', 1)[-1]
        if request.method == 'POST':
            self.assertEqual(request.headers['x-upsert'], 'false')
            if self.redirect_upload:
                return httpx.Response(307, headers={'location': 'https://untrusted.example.invalid/'})
            self.objects[key] = request.content
            return httpx.Response(200, json={'Key': 'roadmap-evidence/' + key})
        if request.method == 'DELETE':
            self.objects.pop(key, None)
            return httpx.Response(200, json={'message': 'Successfully deleted'})
        self.assertIn('/object/authenticated/', request.url.path)
        return httpx.Response(200, content=self.objects[key]) if key in self.objects else httpx.Response(404)

    def upload(self, task):
        return self.client.post('/api/tasks/' + task['id'] + '/advance-file',
                                data={'revision': str(task['revision']), 'progress': '60', 'comment': 'Entrega privada'},
                                files={'file': ('informe ágil.txt', b'Contenido privado', 'text/plain')})

    def test_remote_upload_preview_notification_and_access_before_provider_fetch(self):
        task = self.task(responsible_id=self.member.id)
        self.sign_in('member@example.invalid')
        result = self.upload(task)
        self.assertEqual(result.status_code, 200, result.text)
        file = result.json()['latest_evidence_file']
        self.assertEqual(len(self.objects), 1)
        self.assertEqual(self.client.get(file['url']).content, b'Contenido privado')
        self.assertEqual(self.client.get(file['url'] + '/preview').json()['text'], 'Contenido privado')
        self.assertNotIn('supabase', str(file))
        self.client.cookies.clear()
        before = len(self.requests)
        self.assertEqual(self.client.get(file['url']).status_code, 401)
        self.assertEqual(len(self.requests), before)
        self.sign_in('reader@example.invalid')
        before = len(self.requests)
        self.assertEqual(self.client.get(file['url']).status_code, 403)
        self.assertEqual(len(self.requests), before)
        self.sign_in()
        self.assertEqual(self.client.get(file['url']).content, b'Contenido privado')
        self.assertTrue(any(item.get('task_id') == task['id'] for item in self.client.get('/api/alerts').json()))

    def test_failed_database_commit_removes_remote_object(self):
        task = self.task()
        with patch('app.task_routes.record_advance', side_effect=RuntimeError('Fallo ficticio')):
            with self.assertRaises(RuntimeError):
                self.upload(task)
        self.assertEqual(self.objects, {})
        self.assertTrue(any(method == 'DELETE' for method, _ in self.requests))

    def test_public_bucket_and_redirect_cannot_receive_evidence(self):
        task = self.task()
        self.public = True
        self.assertEqual(self.upload(task).status_code, 503)
        self.assertFalse(any(method == 'POST' for method, _ in self.requests))
        self.public = False
        self.redirect_upload = True
        self.assertEqual(self.upload(task).status_code, 503)
        self.assertEqual(self.objects, {})

    def test_missing_oversized_and_corrupted_remote_bytes_are_rejected(self):
        task = self.task()
        result = self.upload(task)
        self.assertEqual(result.status_code, 200, result.text)
        url = result.json()['latest_evidence_file']['url']
        key = next(iter(self.objects))
        self.objects[key] = b'X' * len(b'Contenido privado')
        self.assertEqual(self.client.get(url).status_code, 404)
        self.objects[key] += b'X'
        self.assertEqual(self.client.get(url).status_code, 404)
        self.objects.clear()
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_endpoint_is_https_supabase_only_and_legacy_auth_is_supported(self):
        with patch.object(settings, 'supabase_url', 'https://attacker.example.invalid'):
            with self.assertRaises(Exception) as error:
                remote_config()
            self.assertEqual(error.exception.status_code, 503)
        with patch.object(settings, 'supabase_service_key', SecretStr('legacy-jwt-ficticio')):
            self.assertEqual(remote_config()[2]['Authorization'], 'Bearer legacy-jwt-ficticio')
