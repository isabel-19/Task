from pydantic_settings import BaseSettings, SettingsConfigDict


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

    @property
    def origins(self):
        return [x.strip() for x in self.frontend_origins.split(',') if x.strip()]


settings = Settings()
if settings.app_env == 'production':
    if settings.demo_mode or not settings.cookie_secure or not settings.database_url.startswith('postgresql'):
        raise RuntimeError('Producción requiere PostgreSQL, DEMO_MODE=false y COOKIE_SECURE=true.')
