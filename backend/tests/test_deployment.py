import tempfile
import os
import unittest
from unittest.mock import patch
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, event
from sqlalchemy.orm import Session
from app.db import Base
from app import models as m
from app.bootstrap import initialize
from app.security import permissions, roles, verify_password
from app.web import mount_frontend
from app.deploy import prepare
from app.config import Settings, apply_render_origin


class WebDeploymentTest(unittest.TestCase):
    def test_direct_navigation_and_private_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'dist'
            root.mkdir()
            (root / 'index.html').write_text('<html>ROADMAP</html>')
            (root / 'app.js').write_text('console.log("ready")')
            (Path(directory) / 'secret.txt').write_text('private')
            app = FastAPI()
            @app.get('/api/health')
            def health():
                return {'status': 'ok'}
            mount_frontend(app, str(root))
            with TestClient(app) as client:
                for route in ('/', '/tareas', '/cuentas'):
                    response = client.get(route)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn('ROADMAP', response.text)
                self.assertEqual(client.get('/api/health').json(), {'status': 'ok'})
                for route in ('/api/missing', '/assets/missing.js', '/.env', '/%2e%2e/secret.txt'):
                    response = client.get(route)
                    self.assertEqual(response.status_code, 404, route)
                    self.assertNotIn('private', response.text)
                self.assertIn('console.log', client.get('/app.js').text)
                self.assertEqual(client.post('/tareas').status_code, 405)

    def test_missing_build_fails_instead_of_publishing_empty_site(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(RuntimeError):
                mount_frontend(FastAPI(), directory)


class BootstrapTest(unittest.TestCase):
    def test_first_chief_permissions_no_demo_and_no_overwrite(self):
        engine = create_engine('sqlite://')
        @event.listens_for(engine, 'connect')
        def fk(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            # These two permissions already exist after Alembic 002.
            db.add_all([m.Permission(name='tasks.supervise'), m.Permission(name='tasks.team_read')])
            db.commit()
            chief = initialize(db, 'Jefatura', 'chief@example.invalid', 'Prueba-privada-2026!')
            self.assertEqual(roles(db, chief), ['jefatura'])
            self.assertTrue(verify_password('Prueba-privada-2026!', chief.password_hash))
            self.assertIn('admin.write', permissions(db, chief))
            self.assertIn('tasks.supervise', permissions(db, chief))
            member = m.User(name='Integrante', email='member@example.invalid', password_hash='unused')
            db.add(member)
            db.flush()
            role = db.scalar(select(m.Role).where(m.Role.name == 'integrante'))
            db.add(m.UserRole(user_id=member.id, role_id=role.id))
            db.commit()
            self.assertIn('tasks.write', permissions(db, member))
            self.assertNotIn('admin.write', permissions(db, member))
            self.assertNotIn('tasks.supervise', permissions(db, member))
            self.assertEqual(list(db.scalars(select(m.Task))), [])
            with self.assertRaises(ValueError):
                initialize(db, 'Otra jefatura', 'another@example.invalid', 'Otra-clave-2026!')
            self.assertTrue(verify_password('Prueba-privada-2026!', db.get(m.User, chief.id).password_hash))
        engine.dispose()


class FreeHostStartupTest(unittest.TestCase):
    def test_actual_render_origin_sets_defaults_without_overriding_custom_domain(self):
        config = Settings(_env_file=None, app_env='production')
        apply_render_origin(config, 'https://assigned-example.onrender.com/')
        self.assertEqual(config.origins, ['https://assigned-example.onrender.com'])
        self.assertEqual(config.cloud_public_api_url, 'https://assigned-example.onrender.com/api')
        custom = Settings(_env_file=None, app_env='production', frontend_origins='https://office.example.invalid',
                          cloud_frontend_url='https://office.example.invalid', cloud_public_api_url='https://office.example.invalid/api')
        apply_render_origin(custom, 'https://assigned-example.onrender.com')
        self.assertEqual(custom.origins, ['https://office.example.invalid'])
        self.assertEqual(custom.cloud_frontend_url, 'https://office.example.invalid')

    def test_invalid_host_origin_cannot_replace_allowed_origins(self):
        for origin in ('http://assigned-example.onrender.com', 'https://attacker.example.invalid',
                       'https://assigned-example.onrender.com/path', 'https://user:secret@assigned-example.onrender.com'):
            with self.subTest(origin=origin), self.assertRaises(RuntimeError):
                apply_render_origin(Settings(_env_file=None, app_env='production'), origin)
        development = Settings(_env_file=None, app_env='development')
        previous = development.frontend_origins
        apply_render_origin(development, 'https://assigned-example.onrender.com')
        self.assertEqual(development.frontend_origins, previous)

    def test_initial_account_survives_restart_without_password_reset(self):
        engine = create_engine('sqlite://')
        Base.metadata.create_all(engine)
        configuration = {'BOOTSTRAP_EMAIL': 'chief@example.invalid', 'BOOTSTRAP_NAME': 'Jefatura',
                         'BOOTSTRAP_PASSWORD': 'Primera-clave-privada-2026!'}
        with patch.dict(os.environ, configuration, clear=True), patch('app.deploy.SessionLocal', side_effect=lambda: Session(engine)):
            prepare()
            os.environ['BOOTSTRAP_PASSWORD'] = 'Otra-clave-que-no-debe-aplicarse-2026!'
            prepare()
        with Session(engine) as db:
            users = list(db.scalars(select(m.User)))
            self.assertEqual(len(users), 1)
            self.assertTrue(verify_password(configuration['BOOTSTRAP_PASSWORD'], users[0].password_hash))
            self.assertEqual(roles(db, users[0]), ['jefatura'])
        engine.dispose()

    def test_release_migrations_target_separate_database(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'migrations.db'
            runtime = Path(directory) / 'runtime.db'
            with patch.dict(os.environ, {'RUN_MIGRATIONS': 'true', 'APP_ENV': 'development', 'DEMO_MODE': 'true',
                                         'BOOTSTRAP_EMAIL': '', 'BOOTSTRAP_PASSWORD': '',
                                         'DATABASE_URL': 'sqlite:///' + runtime.as_posix(),
                                         'MIGRATION_DATABASE_URL': 'sqlite:///' + target.as_posix()}):
                prepare()
            self.assertFalse(runtime.exists())
            engine = create_engine('sqlite:///' + target.as_posix())
            with engine.connect() as db:
                self.assertEqual(db.exec_driver_sql('SELECT version_num FROM alembic_version').scalar(), '011')
                self.assertEqual(db.exec_driver_sql('SELECT count(*) FROM users').scalar(), 0)
            engine.dispose()
