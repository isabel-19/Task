"""One application registration, personal authorization for every permitted user."""
import re
from urllib.parse import urlparse
from fastapi import HTTPException
from . import models as m
from .config import settings

FIELDS = ('cloud_public_api_url', 'cloud_frontend_url', 'google_client_id',
          'google_client_secret', 'google_picker_api_key', 'google_project_number',
          'microsoft_client_id', 'microsoft_client_secret', 'microsoft_tenant')
SECRETS = {'google_client_secret', 'microsoft_client_secret', 'google_picker_api_key'}


def values(db=None):
    result = {name: getattr(settings, name) for name in FIELDS}
    if db is not None:
        row = db.get(m.CloudConfiguration, 'application')
        if row:
            from .cloud_accounts import decrypt
            result.update(decrypt(row.settings_ciphertext))
    return result


def valid_urls(config):
    try:
        api = urlparse(config['cloud_public_api_url'])
        ui = urlparse(config['cloud_frontend_url'])
        for parsed in (api, ui):
            if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
                return False
            if parsed.port is not None and parsed.port < 1:
                return False
            if parsed.scheme != 'https' and not (settings.app_env != 'production' and parsed.scheme == 'http' and parsed.hostname in {'localhost', '127.0.0.1'}):
                return False
    except ValueError:
        return False
    return (api.path.rstrip('/') == '/api' and ui.path in {'', '/'}
            and config['cloud_frontend_url'].rstrip('/') in settings.origins)


def public_configuration(db):
    from .cloud_accounts import cipher, configured, callback_url
    config = values(db)
    try:
        cipher()
        encryption_ready = True
    except HTTPException:
        encryption_ready = False
    row = db.get(m.CloudConfiguration, 'application')
    return {'revision': row.revision if row else 0,
            'fields': {key: value for key, value in config.items() if key not in SECRETS},
            'saved_secrets': {key: bool(config[key]) for key in SECRETS},
            'encryption_ready': encryption_ready,
            'providers': {provider: {'configured': configured(provider, db),
                                    'callback_url': callback_url(provider, db)}
                          for provider in ('google', 'microsoft')}}


def save_configuration(db, user, revision, changes):
    from .cloud_accounts import encrypt
    row = db.get(m.CloudConfiguration, 'application', with_for_update=True)
    if revision != (row.revision if row else 0):
        raise HTTPException(409, 'La configuración cambió. Actualiza la página antes de guardar.')
    previous = values(db)
    updated = dict(previous)
    for key, value in changes.items():
        if value is not None:
            value = value.strip()
            # Empty password inputs preserve saved credentials.
            if key not in SECRETS or value:
                updated[key] = value
    for name in ('cloud_public_api_url', 'cloud_frontend_url'):
        updated[name] = updated[name].rstrip('/')
    if not valid_urls(updated):
        raise HTTPException(422, 'Indica una dirección API terminada en /api y una dirección de la aplicación autorizada por el servidor. Usa HTTPS o localhost en desarrollo.')
    if not re.fullmatch(r'[a-zA-Z0-9.-]{1,253}', updated['microsoft_tenant']):
        raise HTTPException(422, 'El directorio Microsoft debe ser common o un identificador de directorio válido.')
    if updated['google_project_number'] and not updated['google_project_number'].isdigit():
        raise HTTPException(422, 'El número del proyecto Google debe contener solo dígitos.')
    encrypted = encrypt(updated)
    if row:
        row.settings_ciphertext = encrypted
        row.revision += 1
        row.updated_at, row.modified_by = m.now(), user.id
    else:
        db.add(m.CloudConfiguration(id='application', settings_ciphertext=encrypted, modified_by=user.id))
    from sqlalchemy import delete
    db.execute(delete(m.CloudOAuthState))
    reset = []
    for provider in ('google', 'microsoft'):
        if previous[provider + '_client_id'] != updated[provider + '_client_id'] or (provider == 'microsoft' and previous['microsoft_tenant'] != updated['microsoft_tenant']):
            db.execute(delete(m.CloudAccount).where(m.CloudAccount.provider == provider))
            reset.append(provider)
    db.add(m.Audit(actor_id=user.id, entity='cloud-configuration', record_id='application', action='configure',
                   after={'changed_fields': [key for key in FIELDS if previous[key] != updated[key]], 'reconnect_providers': reset}))
    db.commit()
    return public_configuration(db)
