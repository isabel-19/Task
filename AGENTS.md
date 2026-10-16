# Instrucciones de continuidad del proyecto

## Al comenzar o retomar una sesión

1. Leer `CONTINUIDAD.md` antes de trabajar para conocer el estado actual, las decisiones del usuario y el siguiente paso.
2. Consultar `TASK.md` y los informes enlazados cuando haga falta el historial o la evidencia de una comprobación.
3. Revisar `git status --short` antes de editar. Conservar los cambios existentes y distinguirlos de los nuevos.
4. No interpretar entradas históricas como el estado actual. No asumir que las sesiones de navegador o el estado del alojamiento siguen vigentes: comprobarlos cuando la tarea dependa de ellos.

## Después de cada modificación

Por petición expresa del usuario del 15 de octubre de 2026, mantener un informe de continuidad después de cada modificación coherente del proyecto (código, configuración, despliegue o documentación), sin esperar a que el usuario lo recuerde ni al cierre de sesión.

- Actualizar `CONTINUIDAD.md` con qué cambió, para qué, los archivos o servicios afectados, qué se comprobó y qué falta.
- Añadir una entrada a su bitácora, conservando el historial, y dejar un siguiente paso concreto para otra sesión.
- Actualizar `TASK.md` si cambian el alcance, las casillas de avance o los bloqueos. Enlazar los informes técnicos existentes para evitar duplicarlos.
- Distinguir cambios locales, commits, cambios subidos a GitHub y cambios realmente desplegados. No afirmar que se publicó algo por haberlo guardado en el equipo.
- Registrar las comprobaciones realmente ejecutadas y su alcance: local o remoto. No presentar una comprobación anterior como recién ejecutada ni una nueva sesión como un reinicio del servidor.
- Si se interrumpe una tarea, registrar el punto exacto alcanzado y lo pendiente. Para cambios solo documentales basta revisar enlaces, coherencia y `git diff --check`; no repetir suites funcionales sin motivo.
- No guardar contraseñas, tokens, claves, cookies, cadenas de conexión ni datos privados en estos informes. Mantener los secretos fuera de Git y mencionar únicamente su ubicación cuando sea necesario.

Esta regla se aplica a esta carpeta y sus subdirectorios. Una petición de informe no autoriza por sí sola a crear commits, subir cambios o desplegar.
