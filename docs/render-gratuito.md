# Render gratuito y Supabase gratuito

Opción elegida por el usuario el 15 de octubre de 2026. `render.yaml` publica la interfaz y la API juntas en una instancia Free. Supabase Free conserva PostgreSQL y las evidencias en un bucket privado. Los archivos no dependen del disco temporal de Render. No se contrató infraestructura de pago.

Estado: preparación local implementada; despliegue y conexión real a Supabase pendientes. Render tiene sesión iniciada en el navegador; todavía se necesitan los accesos de GitHub/Supabase y la publicación del código actualizado.

## Recursos y límites

- Render Free: se suspende tras 15 minutos sin tráfico y puede tardar aproximadamente un minuto en despertar. No tiene disco persistente, consola de servicio ni paso previo al despliegue. La aplicación ejecuta migraciones opcionales antes de arrancar, con el usuario de migración separado del de ejecución.
- No se utiliza Render Postgres Free: caduca a los 30 días y no ofrece backups.
- Supabase Free: actualmente 500 MB de base, 1 GB de archivos, límites de transferencia y pausa tras una semana de inactividad. Revisar uso y hacer copias externas; no incluye backups automáticos de base.
- No añadir planes de pago ni desactivar límites de gasto. La infraestructura gratuita es de prueba y no garantiza disponibilidad institucional.

## Preparación de Supabase

1. Crear el proyecto en una organización Free. Guardar la contraseña de base fuera del código y del chat.
2. Crear el bucket `roadmap-evidence` con **Public desactivado**, máximo de archivo de 20 MB y sin políticas públicas de lectura/escritura. El backend verifica que el bucket sea privado antes de cargar o leer. No crear URLs públicas ni conceder permisos de Storage a usuarios anónimos.
3. Obtener la URL del proyecto y una clave secreta del servidor en el gestor del proveedor. Las claves nuevas `sb_secret_…` usan la cabecera `apikey`; las antiguas `service_role` se admiten por compatibilidad. La clave no llega al navegador ni a variables `VITE_*`.
4. Preparar conexiones `postgresql+psycopg://…?sslmode=require`. En proveedores que requieran IPv4, usar el pooler de **sesión**, no el de transacción, para ejecutar migraciones y mantener el comportamiento del ORM.
5. Aplicar las migraciones hasta 010 y los permisos de `database/supabase-hardening.sql`, revisando el usuario `roadmap_api`. El esquema `roadmap` debe permanecer fuera de la API pública. La cuenta de migración necesita DDL; la cuenta de la aplicación necesita únicamente los permisos de operación.

## Variables de Render

Usar el `Dockerfile` de la raíz y seleccionar **Free**. El Blueprint no define discos ni bases de pago.

| Variable | Valor |
| --- | --- |
| `APP_ENV`, `DEMO_MODE`, `COOKIE_SECURE` | `production`, `false`, `true` |
| `DATABASE_URL` | Conexión PostgreSQL del usuario de aplicación |
| `MIGRATION_DATABASE_URL` | Conexión PostgreSQL del usuario que aplica migraciones |
| `RUN_MIGRATIONS` | `true`; el arranque se detiene si fallan |
| `FRONTEND_ORIGINS`, `CLOUD_FRONTEND_URL` | Origen HTTPS real asignado al servicio |
| `CLOUD_PUBLIC_API_URL` | El mismo origen seguido de `/api` |
| `CLOUD_TOKEN_KEY` | Clave Fernet nueva, en secreto del servidor y con copia segura separada |
| `EVIDENCE_STORAGE_BACKEND` | `supabase` |
| `SUPABASE_URL` | URL HTTPS del proyecto Supabase |
| `SUPABASE_STORAGE_BUCKET` | `roadmap-evidence` |
| `SUPABASE_SERVICE_KEY` | Clave secreta del servidor Supabase |
| `EVIDENCE_UPLOADS_ENABLED`, `EVIDENCE_MAX_UPLOAD_MB` | `true`, `20` |
| `IMPORTS_ENABLED` | `false` |
| `BOOTSTRAP_EMAIL`, `BOOTSTRAP_NAME` | Correo y nombre de la jefatura inicial |
| `BOOTSTRAP_PASSWORD` | Contraseña nueva de ROADMAP guardada temporalmente como secreto |

La primera ejecución crea jefatura solo si no existe ningún usuario. Los reinicios no modifican las cuentas ni sus contraseñas. Retirar `BOOTSTRAP_PASSWORD` y las demás variables `BOOTSTRAP_*` después de verificar el primer ingreso. No ejecutar el seed de demostración ni copiar automáticamente las bases, archivos o sesiones locales.

## Comprobación y Google

Antes de compartir la dirección: verificar salud PostgreSQL, ingreso de jefatura/integrante, asignación → evidencia desde equipo → previsualización → aviso → revisión. Reiniciar Render y volver a descargar el archivo para comprobar persistencia. Un usuario ajeno o sin sesión debe ser rechazado antes de contactar Storage.

Registrar la dirección HTTPS final como origen Google, callback `/api/cloud/google/callback` y referente de Picker. Completar la marca y los enlaces de privacidad antes de habilitar autorización general en Google. Cada usuario vuelve a vincular su propia cuenta; publicar ROADMAP no publica sus archivos de Drive.

Los tests de Storage usan un proveedor HTTP simulado y comprueban permisos, bucket privado, rechazo de redirecciones, integridad/tamaño y limpieza de archivos si falla la transacción. La persistencia y los permisos reales del proveedor deben verificarse después del despliegue.

Validación local: suite completa de 100 pruebas del backend correcta. Después se añadieron y comprobaron dos pruebas de arranque gratuito (migración a base separada y cuenta conservada tras reinicio); el archivo de pruebas de despliegue pasó con sus cinco casos. PostgreSQL, Storage remoto y construcción Docker reales continúan pendientes del proveedor.

Fuentes: [Render Free](https://render.com/docs/free), [Supabase Free](https://supabase.com/pricing), [claves del servidor](https://supabase.com/docs/guides/getting-started/api-keys), [acceso privado a Storage](https://supabase.com/docs/guides/storage/security/access-control).
