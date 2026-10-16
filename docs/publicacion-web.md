# Publicación de ROADMAP OGC

Estado al retomar el 15 de octubre de 2026: **aplicación publicada en https://roadmap-ogc.onrender.com** con Render Free y Supabase. Se comprobaron salud de producción con PostgreSQL, ingreso de jefatura y recuperación íntegra de un archivo privado de prueba. La configuración vigente y los pendientes están en [Render gratuito](render-gratuito.md); las instrucciones de pago de este documento son una alternativa histórica.

El usuario eligió después **Render gratuito**. La configuración activa de la raíz usa Render Free y Supabase Free para conservar datos y archivos privados: seguir [Render gratuito](render-gratuito.md). Las instrucciones de disco y consola de este documento corresponden únicamente a la alternativa de pago, que no se aplicará.

La aplicación conserva el inicio de sesión de ROADMAP. Cada integrante ve las tareas permitidas y conecta su propia cuenta de Google. Compartir la dirección web no concede permisos sobre tareas ni archivos de Drive.

## Paquete preparado

- `Dockerfile`: compila Vue y sirve sus archivos desde FastAPI; interfaz y API comparten dominio y usan `/api`. El contenedor utiliza un usuario sin privilegios y exige configuración de producción.
- `.dockerignore`: excluye bases locales, archivos privados, `.env`, contraseñas y evidencias del contexto de construcción.
- `deploy/render.production.yaml`: alternativa de pago sin aplicar, con disco privado en `/var/data/evidence`, sesiones HTTPS y migraciones previas. No crea automáticamente una base. El `render.yaml` de la raíz es la opción gratuita elegida, con Storage privado de Supabase.
- `python -m app.bootstrap`: crea una única cuenta inicial de jefatura y los roles habituales, sin cuentas ni tareas de demostración. Rechaza bases que ya tienen usuarios y pide la contraseña de ROADMAP de forma oculta.

## Configuración del alojamiento

Antes de aplicar el Blueprint se debe revisar y aceptar el coste del servicio, disco y base de datos. Render gratuito no admite discos persistentes; no sirve por sí solo para conservar los archivos de evidencia de este proyecto.

1. Conectar un repositorio privado con este código, sin archivos locales ni secretos. Seleccionar `deploy/render.production.yaml` como ruta del Blueprint y la raíz del repositorio como contexto Docker.
2. Crear o conectar PostgreSQL privado. `DATABASE_URL` debe usar el controlador instalado: `postgresql+psycopg://…`; usar TLS cuando la conexión al proveedor lo requiera. Preparar migraciones con una cuenta autorizada sobre el esquema `roadmap`. Para la operación institucional, separar el usuario de migraciones y el de ejecución según `docs/operacion.md`; el usuario de ejecución no necesita permisos DDL.
3. Definir `FRONTEND_ORIGINS=https://DIRECCION-ASIGNADA`, `CLOUD_FRONTEND_URL=https://DIRECCION-ASIGNADA` y `CLOUD_PUBLIC_API_URL=https://DIRECCION-ASIGNADA/api`. Son marcadores: sustituirlos por la dirección real devuelta por el proveedor.
4. Generar una clave Fernet nueva para `CLOUD_TOKEN_KEY` dentro del gestor de secretos. Conservar una copia segura separada de la base. No reutilizar automáticamente tokens, sesiones ni credenciales de los usuarios locales. Mantener `EVIDENCE_STORAGE_DIR=/var/data/evidence` en el disco persistente y comprobar permisos de escritura del usuario 10001 después del montaje.
5. Ejecutar `python -m alembic upgrade head` antes del primer arranque. El Blueprint usa el paso previo al despliegue. No ejecutar `app.seed` en producción.
6. En una consola interactiva del servicio, ejecutar `python -m app.bootstrap --name "Jefatura OGC" --email CORREO-DE-JEFATURA` y elegir una contraseña nueva. Después registrar los integrantes desde Administración con sus permisos. No publicar las claves de demostración.

## Google y Microsoft con la dirección final

Registrar el origen HTTPS y `/api/cloud/google/callback` en el cliente Google, y el origen HTTPS en las restricciones de la clave Picker; conservar el dominio requerido por Picker. Completar las páginas reales de inicio y privacidad para la marca OAuth y revisar el paso de Prueba a Producción. Mientras Google siga en Prueba, solo pueden autorizar cuentas incluidas en sus usuarios de prueba.

Configurar las credenciales mediante Administración de ROADMAP, con las cuentas personales vinculadas después por cada usuario. El registro de Microsoft y su callback HTTPS requieren su propia configuración; no están activados por publicar el sitio.

## Verificación antes de compartir el enlace

- `/api/health` devuelve PostgreSQL, entorno production y demo false; `/tareas` y `/cuentas` se pueden abrir directamente y recargar.
- Una persona sin sesión no puede consultar tareas ni descargar evidencias. La API conserva sus respuestas JSON; los archivos ausentes no devuelven el HTML de la interfaz.
- Con jefatura e integrante: asignar tarea → adjuntar evidencia → aviso pendiente a jefatura → observar/corregir/validar. Comprobar quién asignó y la separación entre integrantes.
- Reiniciar el servicio y confirmar que registros y archivos siguen disponibles. Verificar backup y restauración de PostgreSQL, disco de evidencias y clave de cifrado.
- Vincular Google desde dos cuentas autorizadas y probar un documento compartido; verificar su contenido y el rechazo de archivos sin permiso.

Las pruebas locales de rutas y alta inicial no sustituyen esta comprobación sobre el servicio publicado. La construcción Docker y PostgreSQL reales también se deben validar en el proveedor: el entorno local actual no tiene Docker ni servidor PostgreSQL.

Validación local de esta preparación: tres pruebas automatizadas nuevas correctas; compilación Vite correcta; interfaz compilada servida desde la aplicación FastAPI con apertura directa de pantallas y JavaScript 200, tareas sin sesión 401 y archivo privado 404. No se publicó el contenido ni se alteraron los usuarios de trabajo.

Fuentes: [discos persistentes de Render](https://render.com/docs/disks), [límites gratuitos](https://render.com/docs/free), [despliegues y paso previo](https://render.com/docs/deploys), [referencia de Blueprints](https://render.com/docs/blueprint-spec).
