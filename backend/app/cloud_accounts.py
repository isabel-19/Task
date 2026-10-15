"""Per-user OAuth connections. Provider tokens never enter application URLs or audit JSON."""
import hmac
import json
import logging
import re
import secrets
import time
from datetime import timedelta
import httpx
from authlib.integrations.httpx_client import OAuth2Client
from authlib.oauth2 import OAuth2Error
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from sqlalchemy import select, delete, func
from . import models as m
from .config import settings
from .security import digest
from .cloud_configuration import values, valid_urls

PROVIDERS = ('google', 'microsoft')
GOOGLE_SCOPE = 'openid email https://www.googleapis.com/auth/drive.file'
MICROSOFT_SCOPE = 'offline_access User.Read Files.Read'


def cipher():
    try:
        return Fernet(settings.cloud_token_key.encode())
    except (ValueError, TypeError):
        raise HTTPException(503, 'Las conexiones de cuentas requieren configuración de administración.')


def encrypt(value):
    return cipher().encrypt(json.dumps(value).encode()).decode()


def decrypt(value):
    try:
        return json.loads(cipher().decrypt(value.encode()))
    except (InvalidToken, ValueError, TypeError):
        raise HTTPException(409, 'La conexión ya no está disponible. Vuelve a vincular tu cuenta.')


def provider_config(provider, db=None):
    if provider not in PROVIDERS:
        raise HTTPException(404, 'Proveedor no disponible.')
    configuration = values(db)
    if provider == 'google':
        return {'client_id': configuration['google_client_id'], 'client_secret': configuration['google_client_secret'],
                'authorize': 'https://accounts.google.com/o/oauth2/v2/auth',
                'token': 'https://oauth2.googleapis.com/token', 'scope': GOOGLE_SCOPE,
                'profile': 'https://openidconnect.googleapis.com/v1/userinfo'}
    tenant = configuration['microsoft_tenant']
    if not re.fullmatch(r'[a-zA-Z0-9.-]{1,253}', tenant):
        raise HTTPException(503, 'La conexión Microsoft requiere configuración de administración.')
    return {'client_id': configuration['microsoft_client_id'], 'client_secret': configuration['microsoft_client_secret'],
            'authorize': f'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize',
            'token': f'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token',
            'scope': MICROSOFT_SCOPE, 'profile': 'https://graph.microsoft.com/v1.0/me'}


def configured(provider, db=None):
    if provider not in PROVIDERS:
        raise HTTPException(404, 'Proveedor no disponible.')
    try:
        config = provider_config(provider, db)
    except HTTPException:
        return False
    configuration = values(db)
    if not all((config['client_id'], config['client_secret'], configuration['cloud_public_api_url'], configuration['cloud_frontend_url'], settings.cloud_token_key)):
        return False
    if provider == 'google' and not (configuration['google_picker_api_key'] and configuration['google_project_number']):
        return False
    if not valid_urls(configuration):
        return False
    try:
        cipher()
    except HTTPException:
        return False
    return True


def require_configured(provider, db):
    if not configured(provider, db):
        raise HTTPException(503, 'Esta conexión está pendiente de habilitación por administración.')


def callback_url(provider, db=None):
    return values(db)['cloud_public_api_url'].rstrip('/') + '/cloud/' + provider + '/callback'


def oauth_client(provider, token=None, db=None):
    config = provider_config(provider, db)
    return OAuth2Client(config['client_id'], config['client_secret'], scope=config['scope'],
                        redirect_uri=callback_url(provider, db), token=token,
                        token_endpoint_auth_method='client_secret_post',
                        code_challenge_method='S256', timeout=25, follow_redirects=False)


def account(db, user, provider):
    require_configured(provider, db)
    item = db.scalar(select(m.CloudAccount).where(m.CloudAccount.user_id == user.id, m.CloudAccount.provider == provider).with_for_update())
    if not item:
        raise HTTPException(409, 'Primero vincula tu cuenta desde Cuentas vinculadas.')
    return item


def public_accounts(db, user):
    accounts = {row.provider: row for row in db.scalars(select(m.CloudAccount).where(m.CloudAccount.user_id == user.id))}
    return [{'provider': provider, 'configured': configured(provider, db), 'connected': provider in accounts,
             'account_label': accounts[provider].account_label if provider in accounts else None}
            for provider in PROVIDERS]


def start_connection(db, user, provider, session_cookie):
    require_configured(provider, db)
    db.execute(delete(m.CloudOAuthState).where(m.CloudOAuthState.expires_at < m.now()))
    count = db.scalar(select(func.count()).select_from(m.CloudOAuthState).where(m.CloudOAuthState.user_id == user.id))
    if count >= 5:
        raise HTTPException(429, 'Hay varias autorizaciones abiertas. Espera unos minutos y vuelve a intentar.')
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(64)
    with oauth_client(provider, db=db) as client:
        extra = {'access_type': 'offline', 'prompt': 'consent', 'include_granted_scopes': 'true'} if provider == 'google' else {'prompt': 'select_account', 'response_mode': 'query'}
        url, _ = client.create_authorization_url(provider_config(provider, db)['authorize'], state=state, code_verifier=verifier, **extra)
    db.add(m.CloudOAuthState(state_hash=digest(state), user_id=user.id, provider=provider,
                            session_hash=digest(session_cookie), verifier_ciphertext=encrypt(verifier),
                            expires_at=m.now() + timedelta(minutes=10)))
    db.commit()
    return url


def finish_connection(db, user, provider, cookie, query):
    require_configured(provider, db)
    state = db.get(m.CloudOAuthState, digest(query.get('state', '')))
    if not state or state.provider != provider or state.user_id != user.id or state.expires_at < m.now() or not hmac.compare_digest(state.session_hash, digest(cookie)):
        raise HTTPException(400, 'La autorización caducó o pertenece a otra sesión. Inicia la conexión nuevamente.')
    verifier = decrypt(state.verifier_ciphertext)
    consumed = db.execute(delete(m.CloudOAuthState).where(m.CloudOAuthState.state_hash == state.state_hash)).rowcount
    db.commit()
    if consumed != 1:
        raise HTTPException(400, 'La autorización ya fue utilizada.')
    if query.get('error') or not query.get('code'):
        return False
    try:
        with oauth_client(provider, db=db) as client:
            token = client.fetch_token(provider_config(provider, db)['token'], code=query['code'], code_verifier=verifier)
            granted = {scope.lower().removeprefix('https://graph.microsoft.com/') for scope in token.get('scope', '').split()}
            needed = 'https://www.googleapis.com/auth/drive.file' if provider == 'google' else 'files.read'
            if needed not in granted:
                raise HTTPException(400, 'No se autorizó el acceso a documentos. Vuelve a conectar y acepta ese permiso.')
            response = client.get(provider_config(provider, db)['profile'])
            response.raise_for_status()
            profile = response.json()
        subject = profile.get('sub') if provider == 'google' else profile.get('id')
        label = profile.get('email') if provider == 'google' else profile.get('mail') or profile.get('userPrincipalName')
        if not subject or not label or (provider == 'google' and profile.get('email_verified') is not True):
            raise HTTPException(400, 'No se pudo verificar la cuenta autorizada.')
        prior = db.scalar(select(m.CloudAccount).where(m.CloudAccount.user_id == user.id, m.CloudAccount.provider == provider).with_for_update())
        if prior and prior.subject == subject and not token.get('refresh_token'):
            token['refresh_token'] = decrypt(prior.token_ciphertext).get('refresh_token')
        safe_token = {key: token[key] for key in ('access_token', 'refresh_token', 'token_type', 'scope', 'expires_at') if token.get(key) is not None}
        if not safe_token.get('access_token'):
            raise HTTPException(400, 'No se recibió autorización para consultar documentos.')
        if prior:
            prior.subject, prior.account_label, prior.token_ciphertext = str(subject), str(label)[:254], encrypt(safe_token)
            prior.revision += 1
            prior.updated_at = m.now()
        else:
            db.add(m.CloudAccount(user_id=user.id, provider=provider, subject=str(subject), account_label=str(label)[:254], token_ciphertext=encrypt(safe_token), modified_by=user.id))
        db.add(m.Audit(actor_id=user.id, entity='cloud-accounts', action='connect', record_id=user.id,
                       after={'provider': provider, 'account': str(label)[:254]}))
        db.commit()
        return True
    except (httpx.HTTPError, OAuth2Error, ValueError, KeyError, TypeError) as error:
        db.rollback()
        # Never log exception messages: provider payloads can contain credentials.
        logging.getLogger(__name__).warning('Cloud connection failed: provider=%s category=%s', provider, type(error).__name__)
        raise HTTPException(502, 'No se pudo completar la conexión. Intenta vincular la cuenta nuevamente.')


def access_token(db, user, provider):
    row = account(db, user, provider)
    token = decrypt(row.token_ciphertext)
    if token.get('expires_at', 0) > time.time() + 90:
        return token['access_token']
    if not token.get('refresh_token'):
        raise HTTPException(409, 'La autorización caducó. Vuelve a vincular tu cuenta.')
    try:
        with oauth_client(provider, token, db=db) as client:
            refreshed = client.refresh_token(provider_config(provider, db)['token'], refresh_token=token['refresh_token'])
        refreshed.pop('id_token', None)
        refreshed.setdefault('refresh_token', token['refresh_token'])
        row.token_ciphertext = encrypt(refreshed)
        row.updated_at = m.now()
        db.commit()
        return refreshed['access_token']
    except (httpx.HTTPError, OAuth2Error, ValueError, KeyError):
        db.rollback()
        raise HTTPException(409, 'La autorización ya no es válida. Vuelve a vincular tu cuenta.')


def disconnect(db, user, provider):
    if provider not in PROVIDERS:
        raise HTTPException(404, 'Proveedor no disponible.')
    db.execute(delete(m.CloudOAuthState).where(m.CloudOAuthState.user_id == user.id, m.CloudOAuthState.provider == provider))
    db.execute(delete(m.CloudAccount).where(m.CloudAccount.user_id == user.id, m.CloudAccount.provider == provider))
    db.add(m.Audit(actor_id=user.id, entity='cloud-accounts', action='disconnect', record_id=user.id, after={'provider': provider}))
    db.commit()
