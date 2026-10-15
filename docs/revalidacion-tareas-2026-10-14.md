# Revalidación de tareas y avisos — 14 de octubre de 2026

Repetición solicitada por el usuario después de implementar los avisos de evidencia a jefatura. Se utilizó la base ficticia aislada en `.local/tasks-simple-qa/demo.db`.

| Comprobación | Resultado |
| --- | --- |
| Backend, unittest completo | 63 pruebas correctas |
| Frontend, Vitest completo | 42 pruebas correctas |
| Compilación de producción | Correcta |
| Revisión de espacios y conflictos, git diff --check | Correcta |

## Recorrido comprobado nuevamente en navegador

1. Jefatura asignó una tarea nueva a dos personas con fecha límite lejana.
2. El destinatario la encontró en Mis tareas y guardó su evidencia al 40 %, sin permiso para editar la asignación.
3. La sesión de jefatura recibió automáticamente el aviso sin recargar la página. El aviso mostró tarea, autor, porcentaje y estado Por revisar.
4. Jefatura cerró e inició sesión: la evidencia siguió pendiente.
5. Desde el aviso, abrió la tarea y dejó observaciones. El aviso se retiró y el aporte observado permaneció en el historial.
6. El integrante consultó la observación y envió una nueva evidencia corregida al 100 %. Se generó otro aviso con el porcentaje actualizado.
7. Jefatura abrió ese aviso, validó la corrección y comprobó que el pendiente se retirara.

Capturas: `.local/tasks-simple-qa/revalidacion-aviso.png` y `.local/tasks-simple-qa/revalidacion-revisada.png`.

No se detectaron fallos funcionales en este recorrido ni se requirieron cambios en el código. Esta verificación corresponde al entorno local SQLite y a las notificaciones dentro de la aplicación. PostgreSQL/Supabase y el despliegue no formaron parte de esta revalidación.
