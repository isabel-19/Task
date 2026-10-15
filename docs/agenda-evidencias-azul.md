# Agenda, evidencias y azul institucional · 14 de octubre de 2026

Tareas y responsables mantiene la asignación a una o varias personas. La interfaz general usa azul institucional; los colores de estado conservan su significado: pendiente y vencida en rojo, en progreso y pendiente de revisión en amarillo, en revisión en azul y cerrada/validada en verde. El texto acompaña siempre al color.

## Recorrido

1. Jefatura asigna la tarea con personas, fecha límite e instrucciones opcionales.
2. Cada integrante entra en Mis tareas y pulsa Añadir evidencia. Indica descripción de su entrega, porcentaje y enlace Drive/Docs con acceso compartido.
3. Enviar evidencia a revisión guarda el envío y lleva directamente al historial. No vuelve a pedir un comentario ni una revisión al integrante.
4. El envío muestra Pendiente de revisión por jefatura. La descripción del participante y la respuesta de jefatura ocupan bloques distintos.
5. Jefatura abre la campana o Evidencias por revisar, pulsa Abrir evidencia y registra su validación u observaciones junto al envío. La respuesta queda visible para el equipo y se retira el pendiente.
6. Nadie puede revisar su propio envío, incluso con rol jefatura o administrador. Otra persona de jefatura debe hacerlo. La API devuelve 403 y la cola personal de revisión excluye los envíos propios. Los permisos administrativos de jefatura se mantienen.

La ficha tiene Resumen, Evidencias y Añadir evidencia cuando la persona está asignada. El avance individual del grupo se consulta desplegando Avance por persona. El porcentaje del equipo continúa siendo el promedio de todos sus participantes.

## Apertura de archivos

El listado y la agenda ofrecen Abrir documento para el último envío y Ver evidencias para consultar el historial completo. Ambos controles tienen acciones distintas: el primero abre el enlace en otra pestaña y el segundo muestra la ficha. Las evidencias del historial usan botones azules grandes.

Las evidencias enlazadas mediante EvidenceLink y los documentos de Registro Digital vinculados mediante TaskDocument también aparecen en la ficha, con su última versión disponible. Si no tienen un enlace registrado se indica explícitamente. No se pierden ni convierten los registros anteriores.

Registro Digital ofrece un botón visible para abrir el documento tanto en el listado como en su ficha.

Los documentos enlazados siguen alojados en Drive/Docs. La aplicación no cambia sus permisos ni verifica automáticamente el acceso a esos archivos. La ampliación de carga desde el equipo permite adjuntar archivos privados y previsualizarlos sin salir de la tarea; consulta el manual actualizado.

## Agenda semanal

Lista y Agenda semanal consultan los mismos permisos, espacios y filtros. La agenda agrupa las tareas por fecha límite de lunes a domingo, destaca Hoy y las vencidas, permite cambiar de semana y volver a la actual. Consulta intervalos de fecha en el servidor, hasta 100 tareas por página; si hay más, presenta paginación.

Las fechas se calculan como días del calendario local para evitar cambios de día por UTC. Se comprueban domingos y semanas entre meses y años. Los enlaces recibidos desde Dashboard con fechas desde/hasta se respetan en la lista.

## Verificación local

68 pruebas backend y 51 frontend correctas, incluida la regresión que comprueba que la ficha pasa al historial después de actualizarse la tarea. Cubren permisos, enlaces, historial, avisos, bloqueo de revisión propia, fechas y navegación semanal; compilación de producción y diff --check correctos. Navegador real con base ficticia aislada y sesiones distintas de integrante y jefatura: asignación múltiple, entrega, espera, aviso, revisión y lectura de respuesta. Escritorio de 1440 px y móvil de 390 px, sin desbordamiento horizontal.

Se comprobó la apertura del enlace en otra pestaña usando un documento ficticio interceptado exclusivamente en el navegador de pruebas. Esto verifica la navegación; no equivale a comprobar permisos de archivos institucionales reales. Capturas locales en `.local/tasks-simple-qa/blue-*.png`.

No requiere migración de base de datos. PostgreSQL y publicación no forman parte de esta verificación.
