# Asignación simple de actividades

El formulario de tareas sigue las columnas de OCTUBRE y TASK-JOGC del ROADMAP. Se escribe una sola actividad/tarea y se selecciona su temática. No se solicita crear o elegir un proyecto por separado.

Campos visibles:

- Temática / eje: desplegable con las etiquetas leídas del Excel.
- Actividad / tarea: texto del trabajo que se asigna.
- Responsable: persona a cargo.
- Apoyo / participantes: otras personas que colaboran, o todo el equipo.
- Plazo (Deadline): fecha límite.
- Oficina (si aplica): desplegable opcional.

Las observaciones/instrucciones están en un apartado plegable opcional. Inicio, prioridad, recurrencia y tarea principal no se solicitan en la asignación normal. Las relaciones de subtarea se conservan cuando la actividad se crea desde una ficha. En edición se conservan los datos internos anteriores; el historial y la revisión del jefe siguen funcionando.

## Desplegables y fuente

Se leyeron 22 etiquetas distintas de las columnas Ejes temáticos/Temática del libro. Se normalizan espacios y se reutilizan ejes existentes cuando coinciden por mayúsculas/tildes. Las denominaciones diferentes se conservan; no se fusionan categorías ni se completa un nombre parcial por inferencia.

Las tres oficinas se obtienen de «Oficina donde se encuentra» en Entregables OS. Esa columna incluye historial con fechas: las líneas fechadas aportan las etiquetas de oficina; las notas completas y sus celdas se conservan como procedencia del catálogo. El formulario no presupone que una oficina es obligatoria para todas las tareas.

El lote `task-catalogs` guarda hash, encabezados/celdas y UUID de ejes. Esta carga crea únicamente opciones de clasificación. No importa actividades, avances, evidencias, estados ni aprobaciones institucionales. El XLSX original no se modifica.

## Persistencia

La API acepta temática, actividad, responsable y plazo como entrada mínima. Conserva las relaciones internas de proyectos para no romper las tareas anteriores: las actividades nuevas se agrupan automáticamente por temática, sin duplicar el nombre de la tarea. Varias tareas con una temática reutilizan esa agrupación. La fecha de inicio se calcula para la tarea nueva; un plazo histórico no produce una fecha de inicio posterior al vencimiento.

Alembic 003 agrega `projects.group_key` y `tasks.office`, conservando las filas anteriores. La pertenencia, permisos, evidencia y validación de avances se mantienen. Oficina/temática se comprueban en el servidor, además de los controles del formulario.

El script `scripts/import-roadmap-catalogs.py --source <ruta.xlsx>` realiza una lectura previa. `--apply` registra el catálogo autorizado; repetir el mismo hash no duplica ejes ni lotes. Los datos leídos permanecen en la base local y almacenamiento ignorado por Git.
