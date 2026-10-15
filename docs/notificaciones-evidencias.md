# Avisos de evidencias para jefatura

Al guardar un avance con evidencia, el envío queda pendiente de revisión. Jefatura y administración reciben un aviso en la campana con tarea, autor, porcentaje y acceso al detalle. También pueden usar Tareas → Evidencias por revisar.

Con la aplicación abierta, los avisos se actualizan cada 30 segundos y al volver a la ventana. Los cambios realizados en la misma sesión actualizan la campana inmediatamente. Las evidencias pendientes al iniciar sesión también se muestran. El aviso permanece hasta que una persona autorizada valida el envío o deja observaciones; abrir la tarea no lo resuelve.

El pendiente se calcula desde los envíos y sus revisiones guardadas, de modo que conserva su estado al cerrar sesión o reiniciar el servicio. No depende de la fecha límite ni de que la tarea esté asignada al jefe. Solo el último avance con evidencia de cada integrante puede revisarse. Un envío más reciente sustituye el aviso anterior de esa persona, y los envíos antiguos sin revisión aparecen como Envío anterior. Los avisos de otros integrantes se conservan por separado. Los comentarios sin evidencia no generan avisos de revisión.

Se usan los permisos de supervisión y validación de tareas. Integrantes y auditoría no reciben avisos de trabajo de jefatura ni pueden abrir el filtro de pendientes de revisión. El historial y las evidencias siguen sujetos a los permisos de la tarea.

La notificación funciona dentro de la aplicación. No necesita migración ni un servicio externo de mensajería.

Desde la revisión del 14 de octubre, los avisos de trabajo excluyen los envíos propios: incluso una persona con rol jefatura o administrador espera a que otra persona de jefatura revise su entrega. La campana abre directamente la pestaña Evidencias. Consulta [agenda y evidencias](agenda-evidencias-azul.md).

## Verificación local

- Pruebas de API: aviso fuera del espacio personal del jefe y con plazo lejano, permisos, persistencia entre consultas, observación/corrección, validación, varios autores y sustitución de envíos anteriores.
- Prueba frontend: actualización del contador, aviso en la campana, navegación a la tarea y retirada del aviso tras revisar.
- Navegador con dos sesiones ficticias: un integrante añadió evidencia; la sesión de jefatura recibió automáticamente el aviso sin recargar, abrió la tarea desde la campana y validó el aporte. El aviso se retiró y permaneció el pendiente del otro integrante.
- Capturas en `.local/tasks-simple-qa/avisos-jefatura.png` y `.local/tasks-simple-qa/aviso-resuelto-jefatura.png`.
