import unittest
from pathlib import Path
from sqlalchemy import select, func
import test_api
from app import models as m
from app.security import permissions, hash_password, roles


class ChiefAdministrationTest(unittest.TestCase):
    setUpClass = classmethod(test_api.APITest.setUpClass.__func__)
    tearDownClass = classmethod(test_api.APITest.tearDownClass.__func__)
    setUp = test_api.APITest.setUp
    tearDown = test_api.APITest.tearDown
    sign_in = test_api.APITest.sign_in
    create = test_api.APITest.create

    def apply_grants(self, db):
        path = Path(__file__).resolve().parents[2] / 'database/migrations/007_chief_administration_sqlite.sql'
        for statement in path.read_text(encoding='utf-8').split(';'):
            if statement.strip(): db.connection().exec_driver_sql(statement)

    def prepare_chief(self):
        with self.factory() as db:
            chief = m.User(name='Jefatura ficticia',email='chief@example.invalid',password_hash=hash_password(test_api.PASSWORD))
            role = m.Role(name='jefatura')
            db.add_all([chief,role]);db.flush()
            assignment = m.UserRole(user_id=chief.id,role_id=role.id)
            db.add(assignment);db.flush()
            self.chief_id,self.chief_role_id,self.chief_assignment_id=chief.id,role.id,assignment.id
            self.apply_grants(db);db.commit()

    def test_migration_grants_admin_access_without_changing_other_roles_or_history(self):
        with self.factory() as db:
            original_users = {user.id:(user.name,user.password_hash) for user in db.scalars(select(m.User))}
            member_grants = permissions(db,db.get(m.User,self.member.id))
            audit_count = db.scalar(select(func.count()).select_from(m.Audit))
        self.prepare_chief()
        with self.factory() as db:
            chief=db.get(m.User,self.chief_id)
            self.assertEqual(permissions(db,chief),permissions(db,db.get(m.User,self.admin.id)))
            self.assertEqual(roles(db,chief),['jefatura'])
            before=db.scalar(select(func.count()).select_from(m.RolePermission))
            self.apply_grants(db);db.commit()
            self.assertEqual(db.scalar(select(func.count()).select_from(m.RolePermission)),before)
            self.assertEqual(permissions(db,db.get(m.User,self.member.id)),member_grants)
            self.assertEqual({user.id:(user.name,user.password_hash) for user in db.scalars(select(m.User)) if user.id!=self.chief_id},original_users)
            self.assertEqual(db.scalar(select(func.count()).select_from(m.Audit)),audit_count)

    def test_chief_can_administer_users_and_roles_and_cannot_remove_own_privilege(self):
        self.prepare_chief()
        session=self.sign_in('chief@example.invalid')
        self.assertIn('admin.write',session['permissions'])
        for resource in ['users','roles','permissions','audit']:
            response=self.client.get('/api/'+resource)
            self.assertEqual(response.status_code,200,response.text)
        user=self.create('users',name='Nuevo integrante ficticio',email='new@example.invalid',password='Clave-ficticia-2026!')
        with self.factory() as db:
            member_role=db.scalar(select(m.Role).where(m.Role.name=='integrante'))
            member_role_id=member_role.id
            own_permission=db.scalar(select(m.RolePermission).where(m.RolePermission.role_id==self.chief_role_id))
            own_permission_id=own_permission.id
        self.create('user-roles',user_id=user['id'],role_id=member_role_id)
        for name,identifier in [('user-roles',self.chief_assignment_id),('role-permissions',own_permission_id)]:
            response=self.client.post('/api/admin/'+name+'/'+identifier+'/revoke')
            self.assertEqual(response.status_code,422,response.text)
        self.sign_in('member@example.invalid')
        self.assertEqual(self.client.get('/api/users').status_code,403)
