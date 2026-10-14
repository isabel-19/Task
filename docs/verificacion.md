# Registro de verificación local

Fecha: 13 de octubre de 2026. Entorno: Windows, Node 24.11.1 y Python 3.14.6. La aplicación conserva datos de demostración y, por autorización posterior del usuario, participantes del XLSX local. El original se leyó sin modificarlo. No se importaron tareas, evidencias ni conformidades institucionales.

| Verificación | Resultado | Alcance |
|---|---|---|
| Build Vue 3 + Quasar / Vite | Correcto | Bundle de producción y activos de fuentes/iconos locales |
| Pruebas backend | 43 correctas | unittest + FastAPI TestClient, SQLite en memoria con FK activas |
| Pruebas frontend | 31 correctas | Vitest, DOM jsdom, componentes, sesión, navegación entre registros y las 11 pantallas con contrato HTTP real de la demostración |
| HTTP sobre servicios locales | Correcto | Login, 40 recursos, dashboard/alertas, 6 CSV, logout y 401 posterior |
| Alembic SQLite desde base vacía | Correcto | Versiones 001 → 002 → 003; 42 tablas; migración aditiva y seed de base nueva/repetido comprobados |
| SQL PostgreSQL | Generado y compilado | 42 tablas, SQL 001 congelado + 002/003 aditivos en esquema privado roadmap; no ejecutado en PostgreSQL |
| Respaldo SQLite | Correcto | Copia consistente, SHA-256 e integrity_check; destino .local/backups |
| Interfaz visual / navegador real | Pendiente | Browser no encontró navegadores conectados; no hay capturas ni prueba manual móvil |
| Supabase y publicación | Pendiente | Faltan instancia, driver PostgreSQL disponible en el entorno y accesos a los servicios |
| Fuentes institucionales / importación | Mapeo estructural revisado; importación pendiente | ROADMAP y dos registros localizados/leídos; pendiente comprobar objetos de REGISTRO DIGITAL y sus Excel enlazados, identidad y fechas |

Flujos comprobados por API: documento recibido → tarea → carta emitida referenciada → envío manteniendo aprobación pendiente → revisión/firma/derivación/aprobación con resolución → evidencia vinculada y versión validada → cierre; reunión → acuerdo → tarea idempotente → evidencia validada → cierre con actualización de cumplimiento.

Los tests también verifican 401/403, CSRF y origen, límite de intentos de login, asignación grupal/Mis tareas, búsqueda/paginación/plazos, conflictos de revisión, duplicados, FK, ciclos de dependencias, cierre condicionado a evidencia y subtareas, versiones inmutables, permisos Drive confirmados por el usuario, recurrencia, conformidad OS, revalidación de modelos, auditoría sin contraseñas, escape de fórmulas CSV e importación con respaldo, validación y procedencia.

La vista Gantt y los selectores de relaciones tienen límites documentados de 100 y 1 000 registros, respectivamente. Las alertas se actualizan dentro de la aplicación; no se envían correos. La cuenta real de Drive, el SSO institucional, la revisión normativa y la continuidad de hosting requieren decisiones y accesos institucionales. Estas limitaciones no se presentan como pruebas realizadas.

`TASK.md` conserva pendientes las casillas que necesitan PostgreSQL/Supabase, materialización de los objetos de REGISTRO DIGITAL o revisión de navegador. Las entidades y API operativas verificadas localmente se marcan con evidencia de SQLite, sin declarar equivalencia con una prueba PostgreSQL. La apertura aislada del respaldo también comprobó FK, versión 001 y conteos de demo.


## Actualización de tareas compartidas

Se leyeron las 27 hojas del XLSX local en modo de solo lectura. Se comprobaron responsable/apoyo/participantes, documentación, enlaces y observaciones: [análisis y pasos de prueba](roles-y-avances.md). No se importaron filas institucionales.

Pruebas adicionales: autoría inmutable, asignación entre integrantes, selección de todo el equipo, vistas personal/recibidas/asignadas/conjunto/equipo, protección de detalle/lookups/CSV/dashboard/alertas/evidencias, avances por autor, evidencia obligatoria, promedio reportado frente a validado, observación/corrección, rechazo de envíos anteriores y revisión duplicada, cierre con último aporte de todos validado al 100 %, permiso exclusivo de jefe, actualización de componentes y revisión desde la interfaz. El CSV de tareas incluye participantes y ambos porcentajes.

La base local pasó de Alembic 001 a 002 después de un respaldo verificado. Se compararon los valores de las columnas existentes en las 39 tablas históricas de negocio y configuración: se conservaron todos. Se añadieron permisos/asignaciones de supervisión y campos de procedencia; no se alteraron los registros históricos de negocio. `integrity_check` y `foreign_key_check` correctos. Las cuentas reales de la demo local se probaron por HTTP: jefatura/administración acceden a equipo; integrante/coordinación reciben 403 para equipo y detalle ajeno. Evidencia técnica local en `.local/qa/role-runtime.json` (ignorada por Git).

La verificación sigue siendo API/DOM/build. La revisión visual y de extremo a extremo en un navegador real permanece pendiente.


## Registro autorizado de participantes

Se registraron 30 nombres normalizados del libro local. Las diferencias de mayúsculas/tildes se unifican; distintas escrituras permanecen separadas y se señalan como posibles variantes. Se conserva la procedencia exacta por celda en el lote de importación. No se toma ese número como un censo de identidades institucionales confirmadas.

Se probaron los 30 accesos locales por HTTP: perfil integrante, trabajo en tareas habilitado y vista Equipo denegada. Los 30 aparecen en los selectores de asignación. El directorio local contiene esos nombres y cuatro cuentas operativas anteriores. Se comprobaron página HTTP 200, 40 recursos y seis CSV. La comparación del respaldo previo con las 41 tablas persistentes (excluyendo sesiones/intentos de acceso) conservó todos los registros existentes. El XLSX original mantiene su SHA-256.

En una copia aislada de la base ya registrada se probó jefatura → asignación a dos participantes importados → avances propios con evidencia → validación del jefe → porcentajes 25/75/100 → cierre. La base de trabajo no recibió esa tarea ni sus evidencias de prueba.

La comprobación visual continúa pendiente: Browser no tenía navegador conectado y el componente nativo de Computer Use no estaba disponible. Las verificaciones realizadas son API, DOM de los componentes y compilación de producción.


## Formulario reducido basado en el Excel

Se eliminaron del formulario de asignación proyecto, inicio, prioridad, recurrencia y tarea principal. Los seis campos visibles son temática, actividad, responsable, plazo, apoyo/participantes y oficina opcional; las observaciones están en un apartado plegable. Se probaron sus entradas mínimas, ausencia de campos redundantes, selección grupal y edición que conserva configuración anterior.

22 etiquetas de temática y tres oficinas se registraron desde las columnas del libro en un lote con hash y celdas de origen. No se importaron actividades ni aprobaciones. Alembic 003 aplicada tras respaldo; los valores de las columnas existentes en las 40 tablas de negocio/configuración se conservaron, excluyendo el control de versión y sesiones/intentos de acceso de la comparación. Integridad y FK correctas.

En una copia aislada de la base con sus catálogos, jefatura creó dos actividades para un participante registrado usando temática, actividad, responsable, plazo y oficina: se guardaron sin seleccionar proyecto/inicio y reutilizaron la agrupación de temática. El participante pudo consultarlas. No se añadieron esas actividades de prueba a la base de trabajo. HTTP de la página 200; 40 recursos y seis CSV comprobados. Evidencia local: `.local/qa/task-form-runtime.json`.
