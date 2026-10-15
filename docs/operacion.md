# Operación, respaldo y publicación de prueba

Estado al 15 de octubre de 2026: ejecución local verificada con SQLite y revisión de navegador realizada en los flujos de tareas y Google. PostgreSQL/Supabase, GitHub y alojamiento público siguen sin un despliegue verificado. Hay un contenedor y una alternativa de Render con almacenamiento persistente preparados; no existe todavía una URL institucional activa. Consulta [publicación web](publicacion-web.md) para la configuración y las comprobaciones pendientes.

El entorno protege `.git` contra escritura dentro del sandbox. El 15 de octubre se autorizó ejecutar `git add` y `git commit` fuera de él y se preparó el código actualizado para Render Free. No se modificaron permisos del directorio. El push al repositorio existente y la publicación se deben comprobar antes de declarar disponible la plataforma.

## Configuración

`backend/.env` contiene entorno, URL de base de datos, orígenes exactos permitidos, cookies seguras, duración de sesión y modo demo. En PostgreSQL el esquema privado es `roadmap`; la API consulta tablas calificadas y la versión de Alembic también se guarda allí. Las migraciones se ejecutan con una cuenta distinta de la cuenta restringida de aplicación.

Para desplegar, primero instalar `requirements-postgres.txt`, aplicar Alembic sobre una base **vacía de prueba**, cargar solo datos ficticios y revisar `database/supabase-hardening.sql`. No exponer `roadmap` en la Data API de Supabase. Crear `roadmap_api` y su contraseña por un canal privado; no se almacena en SQL ni Git. Revisar permisos reales con ese rol. El esquema privado no debe ser accesible por `anon` ni `authenticated`. La API es el único punto de entrada a los datos.

La configuración elegida está en `render.yaml`: Render Free sirve interfaz y API desde el mismo origen y Supabase Free conserva PostgreSQL y evidencias privadas. `RUN_MIGRATIONS=true` ejecuta Alembic antes de abrir el servidor; `MIGRATION_DATABASE_URL` permite separar la cuenta de migración del usuario restringido de `DATABASE_URL`. Las migraciones siguen siendo explícitas fuera de ese modo. Las credenciales solo se configuran en el backend. Consulta [Render gratuito](render-gratuito.md), incluido el alta inicial sin consola interactiva y los límites de ambos proveedores.

Las evidencias de tareas admiten enlaces autorizados, archivos del equipo y copias elegidas con una conexión Google/Microsoft propia. Los archivos se almacenan en un directorio privado local o un bucket privado de Supabase según `EVIDENCE_STORAGE_BACKEND`. La API verifica sesión y acceso a la tarea antes de consultar el archivo; no proporciona URLs públicas de Storage. El servidor comprueba tamaño e integridad al leer. Los enlaces pegados manualmente requieren permisos del proveedor; las copias OAuth se consultan con las credenciales de la persona que las selecciona.

La migración 008 añade `evidence_files` y conserva las versiones anteriores. Instalar `backend/requirements.txt` (incluye python-multipart) y ejecutar `python -m alembic upgrade head` desde backend antes de reiniciar la API local. Con backend `local`, `EVIDENCE_STORAGE_DIR` define el directorio privado; vacío utiliza `backend/storage/evidence`. Con backend `supabase` se requieren URL HTTPS del proyecto, bucket privado y clave secreta del servidor. No cambiar de backend sobre archivos existentes sin trasladarlos y comprobar su integridad. `EVIDENCE_MAX_UPLOAD_MB` establece el límite entre 1 y 50 MB (20 por defecto). `EVIDENCE_UPLOADS_ENABLED=false` deshabilita nuevos archivos, conserva la lectura de los existentes y permite seguir enviando enlaces. La plantilla gratuita habilita archivos mediante Supabase; nunca utiliza el disco efímero de Render para conservarlos.

La migración 009 incorpora cuentas Google/Microsoft por usuario y procedencia de las copias. La 010 añade configuración general cifrada, administrada por jefatura desde Cuentas vinculadas. Los tokens y la configuración se cifran con `CLOUD_TOKEN_KEY`; conservar esta clave en la configuración privada del servidor y respaldarla por separado. Registrar aplicaciones OAuth y redirecciones una sola vez para la oficina según [activación de cuentas](cuentas-google-microsoft.md). Los cambios del panel se aplican sin reinicio y tienen prioridad sobre `.env`. Cada usuario autorizado conecta después su propia cuenta. Los códigos de autorización se retiran de la cadena de consulta antes del registro de acceso del servidor. No activar registros de depuración de HTTP/OAuth ni guardar respuestas de tokens en auditoría.

## Respaldo

SQLite local: detener las escrituras o usar la API `sqlite3.Connection.backup`, disponible en `scripts/backup-demo.py`. Guarda copia y manifiesto SHA-256 en `.local/backups`, ignorado por Git. Verifica `PRAGMA integrity_check` antes de aceptar la copia. El respaldo debe almacenarse también fuera del equipo por un canal institucional autorizado cuando corresponda.

El script anterior respalda la base, no los archivos. Para una copia completa, detener las nuevas entregas y copiar también el directorio `EVIDENCE_STORAGE_DIR` (por defecto `backend/storage/evidence`) junto con la base. Conservar los nombres internos de los archivos. En una restauración aislada, verificar cada `storage_key`, tamaño y SHA-256 de `evidence_files` contra los bytes restaurados antes de habilitar el servicio. Una copia SQL sin los archivos no permite recuperar las evidencias adjuntas.

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
