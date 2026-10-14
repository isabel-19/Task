# Operación, respaldo y publicación de prueba

Estado: ejecución local verificada con SQLite y datos ficticios. PostgreSQL/Supabase, GitHub, Cloudflare Pages y Render no están conectados ni publicados. Hay configuración de despliegue preparada, no una URL institucional activa. La revisión visual en navegador está pendiente porque Browser no encontró un navegador conectado.

El repositorio Git local se inicializó, pero este entorno protege `.git` contra escritura: `git add` no pudo crear `index.lock`. Los archivos del proyecto existen; el commit y la publicación GitHub deben prepararse en un entorno con permisos de escritura. No se modificaron permisos ni se eludió esa restricción.

## Configuración

`backend/.env` contiene entorno, URL de base de datos, orígenes exactos permitidos, cookies seguras, duración de sesión y modo demo. En PostgreSQL el esquema privado es `roadmap`; la API consulta tablas calificadas y la versión de Alembic también se guarda allí. Las migraciones se ejecutan con una cuenta distinta de la cuenta restringida de aplicación.

Para desplegar, primero instalar `requirements-postgres.txt`, aplicar Alembic sobre una base **vacía de prueba**, cargar solo datos ficticios y revisar `database/supabase-hardening.sql`. No exponer `roadmap` en la Data API de Supabase. Crear `roadmap_api` y su contraseña por un canal privado; no se almacena en SQL ni Git. Revisar permisos reales con ese rol. El esquema privado no debe ser accesible por `anon` ni `authenticated`. La API es el único punto de entrada a los datos.

La configuración Render está en `render.yaml`. Las migraciones no se ejecutan automáticamente al arrancar el servidor: requieren la cuenta de migración y una operación controlada previa. Construir frontend con `VITE_API_URL` de Render, publicar `frontend/dist` en Cloudflare Pages y configurar `FRONTEND_ORIGINS` con el origen HTTPS exacto de Pages. `_redirects` resuelve las rutas SPA. No introducir claves de base de datos en el frontend. Si ambos servicios están en dominios distintos, la cookie usa `SameSite=None; Secure`; hay que verificar la política de cookies del navegador. Se recomienda un dominio común o proxy `/api` para el uso institucional.

Las evidencias y documentos se mantienen mediante enlaces autorizados de Drive/Docs. No existe copia pública de los archivos. El sistema registra la confirmación humana de permisos, no verifica Google Drive mediante OAuth. Las cuentas demo no tienen acceso institucional a Drive.

## Respaldo

SQLite local: detener las escrituras o usar la API `sqlite3.Connection.backup`, disponible en `scripts/backup-demo.py`. Guarda copia y manifiesto SHA-256 en `.local/backups`, ignorado por Git. Verifica `PRAGMA integrity_check` antes de aceptar la copia. El respaldo debe almacenarse también fuera del equipo por un canal institucional autorizado cuando corresponda.

PostgreSQL: ejecutar `pg_dump --format=custom --no-owner --schema=roadmap` con la URL en una variable de entorno temporal o configuración protegida de PostgreSQL; nunca incluir la contraseña en argumentos o registros. Respaldar también `backend/storage/imports`, catálogos, migraciones y configuración protegida. No versionar copias de bases ni archivos institucionales en Git.

Restaurar primero en una base aislada de prueba con `pg_restore --no-owner`, aplicar permisos y comprobar: versión de Alembic, conteos, referencias, auditoría y los dos flujos de integración. Invalidar sesiones restauradas y revisar accesos antes de habilitar el servicio. Una copia no se considera útil hasta verificar su restauración. Los planes gratuitos requieren revisar las capacidades de respaldo disponibles: [documentación oficial de backups de Supabase](https://supabase.com/docs/guides/platform/backups).

## Límites de planes gratuitos

Los planes, cuotas y disponibilidad pueden cambiar. Antes de publicar, revisar las páginas oficiales de [Render Free](https://render.com/docs/free), [Cloudflare Pages Limits](https://developers.cloudflare.com/pages/platform/limits/) y [Supabase Backups](https://supabase.com/docs/guides/platform/backups), consultadas el 13 de octubre de 2026.

Render gratuito puede suspender el servicio por inactividad y su almacenamiento local es efímero. Por ello la base se aloja externamente y los respaldos de importación requieren almacenamiento persistente autorizado. La importación debe **deshabilitarse** en Render gratuito mientras no tenga ese almacenamiento; no basta con guardar el hash en PostgreSQL. Pages publica archivos estáticos: no ejecuta FastAPI. Los despliegues de prueba no equivalen a garantía institucional de continuidad. Las fuentes permanecen pendientes de revisión y no deben subirse datos institucionales reales para probar infraestructura.

## Antes de producción institucional

- Validar identidad, roles, permisos por acción, proceso de altas/bajas y recuperación de acceso.
- Ejecutar migraciones y suite de relaciones en PostgreSQL; probar cuentas restringidas y acceso denegado desde la Data API.
- Hacer revisión visual y prueba completa en navegadores institucionales y pantallas móviles.
- Evaluar dominio común/proxy, cookies, TLS, CORS, CSRF, caducidad, rate limiting y registros de infraestructura.
- Revisar fuente/versión/aplicabilidad de cada modelo de calidad y el mapeo de fuentes reales.
- Asegurar respaldo persistente, restauración probada, conservación documental y responsables de operación.
- Confirmar permisos Drive, revocación y tratamiento de información institucional.
- Evaluar MFA/SSO institucional, concurrencia, carga, monitoreo y continuidad antes de habilitar cuentas reales.

La casilla de publicación seguirá pendiente hasta disponer de cuentas y verificar el despliegue. La casilla de extremo a extremo en navegador seguirá pendiente hasta su ejecución real.
