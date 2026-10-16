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

El commit funcional **741fdfb** se subió a `origin/main` y Render confirmó el despliegue **dep-db94fb6k1f9s73eqrfjg** como Deployed. La configuración guardada ya no contiene BOOTSTRAP_*; el ingreso de jefatura siguió funcionando después del despliegue.

La prueba remota utilizó dos contextos de navegador separados, jefatura y un integrante ficticio. Se verificó el aviso privado de invitación, el rechazo de lectura por otra persona, la apertura de la reunión desde la campana y su desaparición de la cola al marcarse leído. Las pruebas HTTP posteriores confirmaron los avisos de cambio de lugar y cancelación. La reunión ficticia quedó cancelada, sus avisos de prueba leídos y la cuenta técnica desactivada; se comprobó que su sesión recibe 401 después de desactivarla.

Salud final: producción, PostgreSQL y demo desactivada. Tras el despliegue se recuperaron de nuevo la tarea ficticia cerrada y el archivo anterior, con hash correcto. El archivo de hardening no forma parte del commit funcional y conserva su cambio local.

Los datos de prueba están identificados como ficticios; no se enviaron invitaciones a personas ajenas al ensayo. Los resultados privados, sin credenciales, están en `.local/release-011-qa-result.json` y `.local/release-011-status.json`.

Las notas finales se guardan en un commit solo documental con `[skip render]`, mecanismo [documentado por Render](https://render.com/docs/deploys#skipping-an-auto-deploy), para no repetir el despliegue ya validado. La funcionalidad publicada corresponde a 741fdfb.
