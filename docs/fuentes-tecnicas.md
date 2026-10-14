# Referencias técnicas

Consultadas el 13 de octubre de 2026 para la implementación:

- Quasar con Vite: https://quasar.dev/start/vite-plugin/
- Seguridad FastAPI: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- ORM SQLAlchemy 2: https://docs.sqlalchemy.org/en/20/orm/quickstart.html
- Restricciones PostgreSQL: https://www.postgresql.org/docs/current/ddl-constraints.html

Se usa sesión opaca revocable en cookie HttpOnly y token CSRF, en lugar de JWT en almacenamiento del navegador.
