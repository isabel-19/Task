# Roles y avances compartidos

Actualización del 14 de octubre: la interfaz de Tareas se simplificó a asignación individual y evidencia desde la ficha. Consulta [el flujo actual](asignacion-simple.md). La descripción de botones de esta revisión anterior es histórica; los permisos y aportes de tareas grupales existentes se conservan.

Referencia leída sin modificar: `ROADMAP OGC 2026 v2.xlsx`, SHA-256 `b65180d05ee01693184bd21e09c55cea70345eac54aedd863d3419fdbc3990c1`. Se revisaron las 27 hojas del libro local. En esta revisión inicial no se importaron datos; después el usuario autorizó el [registro local de participantes](participantes.md). Las tareas y evidencias institucionales no se importaron.

## Estructura observada

En las hojas mensuales, incluida OCTUBRE, fila 2, C identifica participantes, E la actividad/tarea, F al responsable, G el plazo, O documentación, P el enlace, Q observaciones de OGC y R la respuesta. En TASK-JOGC, fila 4, C es responsable, G tarea, H apoyo, I/J inicio y plazo, M estado, N detalle actual, O seguimiento y P enlace. TASK-Asistentes, fila 3, usa B responsable, F tarea, G apoyo, H/I fechas, L estado, M detalle actual, N seguimiento y O enlace. Hay celdas con varias personas en responsable/apoyo/participantes: el modelo necesita asignación múltiple.

La hoja «Roles» organiza temáticas/modelos de calidad; no es un catálogo de permisos de autenticación. La separación entre jefe e integrantes y las vistas personales proviene de la indicación del usuario. La validación individual y el promedio de porcentajes son decisiones de la aplicación; el Excel no demuestra que exista esa fórmula.

## Cómo probarlo

1. Accede a http://127.0.0.1:5173 con `jefatura@example.invalid` y la contraseña de `.local/demo-access.txt`.
2. Crea una tarea con Elena y Mateo como participantes. Puedes usar «Asignar a todo el equipo».
3. Cierra sesión y entra con `integrante@example.invalid`. La tarea aparece en «Me asignaron» y «En conjunto».
4. Abre la tarea y registra tu avance, comentario y enlace de evidencia accesible para el jefe.
5. Vuelve a la cuenta de jefatura, selecciona «Equipo», abre la tarea y revisa el aporte. «Validar avance» registra el porcentaje; «Dejar observaciones» conserva la nota y permite corregir mediante otro envío.
6. Revisa que cada persona conserve su porcentaje. Por defecto el consolidado es el promedio validado del grupo. El cierre se habilita cuando el último aporte de cada integrante está validado al 100 %.

También un integrante puede crear tareas para colegas. «Asigné» conserva las que creó o a las que agregó integrantes. La cuenta de coordinación trabaja como integrante para avances de tareas; la revisión queda reservada a jefatura/administración.
