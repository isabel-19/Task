# Publicación de avisos de reuniones — 16 de octubre de 2026

## Cambio

Al programar una reunión se pueden seleccionar asistentes. Cada persona recibe un aviso privado en la campana; también se avisa al añadir asistentes posteriormente y al cambiar título, fecha, lugar o estado. Al abrir un aviso se marca como leído. La migración 011 añade `roadmap.notifications` y concede al rol de aplicación los permisos necesarios.

## Respaldo antes de migrar

Se preparó con las herramientas PostgreSQL oficiales distribuidas por [EDB](https://www.enterprisedb.com/download-postgresql-binaries?lang=en). El esquema `roadmap` se exportó con pg_dump en una transacción de lectura repetible y un snapshot compartido, antes de tocar producción.

La copia cifrada está en `.local/backups/prod-pre-011-20261016T153301Z/`, fuera de Git: 48 tablas, 257 registros, 3 evidencias verificadas por SHA-256 y claves de recuperación cifradas. Se restauró en PostgreSQL local aislado, se compararon todos los conteos y se comprobaron las FK y la integridad de los archivos. El servidor temporal quedó detenido. No se restauró sobre Supabase ni se borraron registros de producción.

La copia es local. Para recuperación ante pérdida del equipo, conservar una copia privada externa y el material local que permite descifrarla; ninguno se incluye en el repositorio.

## Migración y configuración

- Alembic `upgrade 011` aplicado en Supabase después de verificar el respaldo.
- Versión 011 y nueva tabla confirmadas; permisos SELECT/INSERT/UPDATE del rol `roadmap_api` comprobados; `anon` y `authenticated` siguen sin acceso al esquema.
- Conteos anteriores de usuarios, tareas, reuniones, asistentes y evidencias conservados al comprobar la migración.
- Variables temporales `BOOTSTRAP_EMAIL`, `BOOTSTRAP_NAME` y `BOOTSTRAP_PASSWORD` retiradas del servicio Render mediante Save only. El siguiente despliegue aplica esa configuración y conserva la cuenta existente.
- Por indicación del propietario, `database/supabase-hardening.sql` queda excluido del commit/push. Su cambio local previo se conserva.
- Se mantiene la interfaz servida por FastAPI en el mismo dominio. No se creó un sitio estático separado; se planteó como opción y no hubo confirmación de separación durante esta preparación.

## Validación y publicación

Antes del envío: 109 pruebas backend, 76 frontend y compilación de producción correctas. Las pruebas de reuniones incluyen invitación, cambio/cancelación, asistentes añadidos después, deduplicación, rechazo de inactivos y lectura exclusiva por el destinatario.

Al escribir esta entrada todavía está pendiente confirmar el commit/push, el despliegue de Render y el flujo remoto con dos cuentas. Consultar `CONTINUIDAD.md` para el resultado final; no interpretar este estado intermedio como despliegue confirmado.
