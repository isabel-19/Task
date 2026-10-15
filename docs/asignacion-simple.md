# Asignación simple de tareas

El flujo actual es: asignar una tarea a una o varias personas → el responsable la consulta → registra avances y evidencias → jefatura revisa y cierra. La pantalla se simplificó el 14 de octubre de 2026 por indicación del usuario.

Campos visibles:

- ¿Qué debe hacer?: tarea que se asigna.
- Asignar a: una o varias personas, con búsqueda por nombre.
- Fecha límite: plazo de entrega.
- Instrucciones: detalle opcional.

Cada persona seleccionada encuentra la tarea en «Mis tareas». Quien la asignó la encuentra en «Tareas que asigné». Los perfiles autorizados cuentan con «Todas las tareas». Al abrirla, cada integrante encuentra el formulario «Añadir mi evidencia», escribe lo realizado, su porcentaje y un enlace de Drive/Docs accesible para la persona que revisa. Cada envío se conserva en el historial y su nombre de evidencia se genera automáticamente.

Se retiraron de la interfaz de asignación temática, oficina, apoyo e inicio. Las personas se seleccionan en un único campo múltiple. Al editar se conservan la clasificación, oficina, participantes y configuración anteriores. La pertenencia, las revisiones y el historial de las tareas grupales ya registradas se conservan.

## Catálogos anteriores y fuente

Se leyeron 22 etiquetas distintas de las columnas Ejes temáticos/Temática del libro. Se normalizan espacios y se reutilizan ejes existentes cuando coinciden por mayúsculas/tildes. Las denominaciones diferentes se conservan; no se fusionan categorías ni se completa un nombre parcial por inferencia.

Las tres oficinas se obtienen de «Oficina donde se encuentra» en Entregables OS. Esa columna incluye historial con fechas: las líneas fechadas aportan las etiquetas de oficina; las notas completas y sus celdas se conservan como procedencia del catálogo. El formulario no presupone que una oficina es obligatoria para todas las tareas.

El lote `task-catalogs` guarda hash, encabezados/celdas y UUID de ejes. Esta carga crea únicamente opciones de clasificación. No importa actividades, avances, evidencias, estados ni aprobaciones institucionales. El XLSX original no se modifica.

## Persistencia

La API acepta tarea, responsable y plazo como entrada mínima, con asignaciones adicionales en member_ids. El selector múltiple se guarda en una sola operación. Las asignaciones directas se agrupan internamente en «Tareas generales». Las integraciones que suministran temática o proyecto conservan su clasificación. La fecha de inicio se calcula para la tarea nueva; un plazo histórico no produce una fecha de inicio posterior al vencimiento. Esta simplificación no necesita migración.

Alembic 003 agrega `projects.group_key` y `tasks.office`, conservando las filas anteriores. La pertenencia, permisos, evidencia y validación de avances se mantienen. Oficina/temática se comprueban en el servidor, además de los controles del formulario.

El script `scripts/import-roadmap-catalogs.py --source <ruta.xlsx>` realiza una lectura previa. `--apply` registra el catálogo autorizado; repetir el mismo hash no duplica ejes ni lotes. Los datos leídos permanecen en la base local y almacenamiento ignorado por Git.

La [verificación del flujo simplificado](tareas-simplificadas-2026-10-14.md) registra pruebas y revisión de navegador.
