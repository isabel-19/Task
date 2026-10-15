# Tareas y responsables — 14 de octubre de 2026

La pantalla se centra en asignar a una o varias personas y permitir que esa persona documente su trabajo desde la tarea.

## Interfaz

- Asignación: qué deben hacer, una o varias personas seleccionadas, fecha límite e instrucciones opcionales.
- Vistas: Mis tareas, Tareas que asigné y Todas las tareas para los perfiles autorizados.
- Listado: tarea, personas asignadas, fecha límite, avance reportado y estado.
- Ficha: responsable, plazo, autor de asignación, instrucciones y avances con sus evidencias.
- Avance: descripción, porcentaje y enlace Drive/Docs con confirmación de acceso. Nombre de evidencia automático; varios envíos el mismo día conservan sus registros independientes.
- Revisión y cierre: jefatura valida u observa el último aporte. Con el 100 % validado, puede confirmar el cierre utilizando la evidencia ya registrada.

Se retiraron de esta pantalla temática, oficina, directorio, pestañas de asignaciones/avances/cierres, campos internos, filtros de año/proceso y vistas redundantes. La configuración y las relaciones de las tareas anteriores se conservan. Las tareas compartidas muestran a todas las personas asignadas y exigiendo su validación para cerrar.

La API mantiene permisos y comprobaciones de evidencia, revisión, concurrencia y cierre. La asignación directa se agrupa internamente en Tareas generales. La ampliación posterior permite adjuntar archivos privados del equipo además de enlaces; requiere la migración 008. Consulta el manual actualizado. Los permisos de Drive no se verifican automáticamente.

## Verificación

- 61 pruebas backend y 41 frontend correctas; build de producción correcto.
- Navegador real sobre una base ficticia separada: jefatura asignó a una persona; esta consultó Mis tareas y registró 50 % y 100 % con dos evidencias el mismo día; jefatura revisó el último aporte y cerró la tarea.
- El integrante no recibió controles para validar aportes. La API rechazó el detalle para un usuario ajeno.
- Revisión visual de listado en 1440, 768, 390 y 320 px sin desbordamiento horizontal; formulario y ficha comprobados en escritorio y móvil.
- Capturas locales en `.local/tasks-simple-qa/` (ignoradas por Git). Las evidencias usan enlaces ficticios y no se abrieron como documentos reales.
- PostgreSQL/Supabase y despliegue continúan pendientes.

## Corrección de asignación compartida y evidencia visible

El selector Asignar a admite varias personas. El listado ofrece Añadir evidencia para cada integrante. En la ficha, el formulario Añadir mi evidencia está visible aunque esa persona no pueda editar la asignación. Añadir personas conserva los integrantes y aportes anteriores. El filtro por persona incluye también las asignaciones adicionales.

Adjuntar desde una tarea requiere pertenecer a ella y tener permiso de trabajo en tareas. No exige administrar el catálogo general de Evidencias. La prueba de permisos comprueba que un integrante puede aportar desde la tarea mientras la creación directa en ese catálogo sigue denegada.

En navegador se creó una tarea para Elena y Mateo: ambos entraron con su propia cuenta, ninguno tenía permiso para editarla y guardaron evidencias independientes al 40 % y 70 %. El historial conservó autores, enlaces y porcentajes de ambos. Las pruebas usaron la base ficticia aislada.
