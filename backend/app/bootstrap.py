"""Create the first chief and standard roles on a migrated, user-empty database."""
import argparse
from getpass import getpass
from sqlalchemy import select
from . import models as m
from .catalog import MODULES
from .db import SessionLocal
from .security import hash_password


def initialize(db, name, email, password):
    name, email = name.strip(), email.strip().lower()
    if not name or len(name) > 160 or len(email) > 254 or email.count('@') != 1 or any(c.isspace() for c in email):
        raise ValueError('Indica un nombre y correo válidos para jefatura.')
    if not 12 <= len(password) <= 256:
        raise ValueError('La contraseña debe tener entre 12 y 256 caracteres.')
    if db.scalar(select(m.User.id).limit(1)):
        raise ValueError('La base ya tiene usuarios. No se modificó ninguna cuenta.')
    chief = m.User(name=name, email=email, password_hash=hash_password(password))
    db.add(chief)
    db.flush()
    chief.modified_by = chief.id
    names = [f'{module}.{action}' for module in MODULES for action in ('read', 'write', 'validate')]
    names += ['tasks.supervise', 'tasks.team_read']
    existing = {p.name: p for p in db.scalars(select(m.Permission))}
    for permission_name in names:
        if permission_name not in existing:
            permission = m.Permission(name=permission_name, modified_by=chief.id)
            db.add(permission)
            existing[permission_name] = permission
    db.flush()
    for role_name in ('administrador', 'jefatura', 'coordinador', 'integrante', 'consulta_auditoria'):
        role = db.scalar(select(m.Role).where(m.Role.name == role_name))
        if not role:
            role = m.Role(name=role_name, modified_by=chief.id)
            db.add(role)
            db.flush()
        grants = set(db.scalars(select(m.RolePermission.permission_id).where(m.RolePermission.role_id == role.id)))
        for permission_name, permission in existing.items():
            if permission_name not in names:
                continue
            module, action = permission_name.split('.')
            allowed = role_name in ('administrador', 'jefatura')
            if role_name == 'coordinador':
                allowed = module != 'admin' and (module != 'audit' or action == 'read')
            elif role_name == 'integrante':
                allowed = module not in ('admin', 'audit') and action in ('read', 'write') and (module != 'reports' or action == 'read')
            elif role_name == 'consulta_auditoria':
                allowed = module != 'admin' and action == 'read'
            if permission_name == 'tasks.supervise':
                allowed = role_name in ('administrador', 'jefatura')
            elif permission_name == 'tasks.team_read':
                allowed = role_name == 'consulta_auditoria'
            if allowed and permission.id not in grants:
                db.add(m.RolePermission(role_id=role.id, permission_id=permission.id, modified_by=chief.id))
        if role_name == 'jefatura':
            db.add(m.UserRole(user_id=chief.id, role_id=role.id, modified_by=chief.id))
    db.add(m.Audit(actor_id=chief.id, entity='users', record_id=chief.id, action='bootstrap', after={'role': 'jefatura'}))
    db.commit()
    return chief


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument('--email', required=True)
    args = parser.parse_args()
    password = getpass('Nueva contraseña de ROADMAP (no la de Google): ')
    if password != getpass('Repite la contraseña: '):
        raise SystemExit('Las contraseñas no coinciden.')
    with SessionLocal() as db:
        try:
            initialize(db, args.name, args.email, password)
        except ValueError as error:
            raise SystemExit(str(error)) from None
    print('Jefatura creada. No se cargaron cuentas ni tareas de demostración.')


if __name__ == '__main__':
    main()
