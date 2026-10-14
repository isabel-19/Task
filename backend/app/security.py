import hashlib
import hmac
import secrets
from datetime import timedelta
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from .db import get_db
from .models import User, UserRole, Role, RolePermission, Permission, LoginSession, now
from .config import settings


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    return f'scrypt${salt}${digest}'


def verify_password(password, encoded):
    try:
        _, salt, expected = encoded.split('$')
        actual = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def permissions(db, user):
    return set(db.scalars(select(Permission.name).join(RolePermission, Permission.id == RolePermission.permission_id)
                         .join(UserRole, RolePermission.role_id == UserRole.role_id).where(UserRole.user_id == user.id)))


def roles(db, user):
    return list(db.scalars(select(Role.name).join(UserRole, Role.id == UserRole.role_id).where(UserRole.user_id == user.id)))


def current_user(request: Request, db=Depends(get_db)):
    token = request.cookies.get('ogc_session', '')
    session = db.get(LoginSession, digest(token)) if token else None
    user = db.get(User, session.user_id) if session and session.expires_at > now() else None
    if not user or not user.active:
        raise HTTPException(401, 'Inicia sesión para continuar.')
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        origin = request.headers.get('origin')
        if origin and origin not in settings.origins:
            raise HTTPException(403, 'Origen no autorizado.')
        if not hmac.compare_digest(session.csrf_hash, digest(request.headers.get('x-csrf-token', ''))):
            raise HTTPException(403, 'La sesión requiere un token CSRF válido.')
    return user


def require(db, user, permission):
    if permission not in permissions(db, user):
        raise HTTPException(403, 'Tu perfil no permite esta acción.')


def new_session(db, user):
    token = secrets.token_urlsafe(32)
    csrf = digest(token + ':csrf')
    db.add(LoginSession(id=digest(token), user_id=user.id, csrf_hash=digest(csrf), expires_at=now() + timedelta(hours=settings.session_hours)))
    return token, csrf
