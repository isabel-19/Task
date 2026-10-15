from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    app_env: str = 'development'
    database_url: str = 'sqlite:///./roadmap-demo.db'
    frontend_origins: str = 'http://localhost:5173,http://127.0.0.1:5173'
    cookie_secure: bool = False
    demo_mode: bool = True
    session_hours: int = 8
    demo_password: str = ''
    imports_enabled: bool = True
    evidence_storage_dir: str = ''
    evidence_max_upload_mb: int = 20
    evidence_uploads_enabled: bool = True
    evidence_storage_backend: str = 'local'
    supabase_url: str = ''
    supabase_storage_bucket: str = 'roadmap-evidence'
    supabase_service_key: SecretStr = SecretStr('')
    frontend_dist: str = ''
    cloud_token_key: str = ''
    cloud_public_api_url: str = ''
    cloud_frontend_url: str = ''
    google_client_id: str = ''
    google_client_secret: str = ''
    google_picker_api_key: str = ''
    google_project_number: str = ''
    microsoft_client_id: str = ''
    microsoft_client_secret: str = ''
    microsoft_tenant: str = 'common'

    @property
    def origins(self):
        return [x.strip() for x in self.frontend_origins.split(',') if x.strip()]


settings = Settings()
if settings.app_env == 'production':
    if settings.demo_mode or not settings.cookie_secure or not settings.database_url.startswith('postgresql'):
        raise RuntimeError('Producción requiere PostgreSQL, DEMO_MODE=false y COOKIE_SECURE=true.')
