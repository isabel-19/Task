# Jefatura con nivel de administrador

Por indicación del usuario, Jefatura tiene el mismo nivel de acceso que Administrador. El rol conserva el nombre jefatura y permite gestionar usuarios, asignaciones de roles, catálogos e importaciones, consultar auditoría y operar todos los módulos. Mantiene la supervisión de tareas, los avisos de evidencias, las revisiones y los cierres.

La migración aditiva 007 incorpora a jefatura los permisos del rol administrador que le faltaban. No crea cuentas, no cambia contraseñas ni modifica las tareas o evidencias existentes. Repetir el SQL no duplica asignaciones. Las instalaciones nuevas crean ambos roles con los mismos permisos.

Los integrantes, coordinación y auditoría conservan sus permisos. La aplicación no deduce quién es jefe por su nombre: se utiliza la asignación del rol jefatura. Los controles de sesión y permisos siguen aplicándose en la API.

Las protecciones administrativas también se aplican a jefatura: no se puede retirar el propio rol administrativo, desactivar la propia cuenta ni retirar permisos de los roles protegidos de administración y jefatura. Los cambios de permisos se reflejan en la interfaz al recargar la página o iniciar sesión nuevamente.

## Verificación

- Prueba de migración: permisos equivalentes, asignaciones idempotentes, usuarios y contraseñas anteriores conservados, otros roles sin cambios.
- Prueba de API: una cuenta con rol jefatura accede a usuarios/roles/permisos/auditoría, crea un usuario y le asigna el rol integrante. La retirada del propio acceso se rechaza; los integrantes siguen recibiendo 403 para Administración.
- Prueba de instalación nueva: jefatura y administrador reciben los mismos permisos.
- Comprobación de las tres bases locales (trabajo, revisión y QA): versión 007, 34 permisos para jefatura y 34 para administrador, registros anteriores conservados y claves foráneas correctas. Respaldo con SHA-256 por base.
- Navegador: una cuenta jefatura accedió a Administración y abrió el formulario de creación de usuarios. Captura ficticia en `.local/tasks-simple-qa/jefatura-administracion.png`.
- Verificación completa: 65 pruebas backend y 42 frontend correctas.
- La migración local se aplica tras respaldo consistente, comprobación de registros anteriores y claves foráneas. Los respaldos y manifiestos permanecen en `.local/backups/`.
- El SQL PostgreSQL se incluye para ese entorno; su ejecución en PostgreSQL/Supabase continúa pendiente.
