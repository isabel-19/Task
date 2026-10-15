# Auditoría funcional y visual de TASK PAGINA WEB

**Fecha:** 13 de octubre de 2026, America/Lima.<br>
**Aplicación:** ROADMAP OGC · UNAJMA.<br>
**Resultado:** 12 hallazgos confirmados: 1 de prioridad alta, 9 de prioridad media y 2 de prioridad baja. Los flujos principales funcionan, pero la paginación, algunas búsquedas y el tratamiento de fechas necesitan correcciones.

## Método y entorno

Se realizaron pruebas reales en Google Chrome mediante Playwright, con navegación, clics, escritura, envío de formularios, apertura de fichas, descargas y capturas. Se registraron respuestas HTTP, errores de consola y excepciones JavaScript. La inspección del código se utilizó después para localizar las áreas relacionadas con los problemas reproducidos.

Playwright MCP no estaba conectado en la sesión. El navegador integrado tampoco tenía una conexión disponible. Tras la autorización para continuar, se instaló Playwright en `.local/audit-tools` y se ejecutó Chrome local en modo headless. **Estas pruebas usaron Playwright local, no Playwright MCP.**

| Elemento | Entorno comprobado |
|---|---|
| Servidor original | `http://127.0.0.1:5173` |
| API original | `http://127.0.0.1:8000/api/health`, HTTP 200, estado `ok` |
| Copia para pruebas que guardan datos | Frontend 5174 y API 8001, mismo código y copia consistente de SQLite |
| Automatización | Playwright 1.64.0 |
| Navegador | Google Chrome 155.0.8059.79 |
| Escritorio y tablet | Anchos 1440 y 768 px |
| Pantallas estrechas | Anchos 390 y 320 px; login adicionalmente a 375 px |
| Emulación móvil | Perfil iPhone 13 de Playwright, con viewport 390 × 664 y comportamiento móvil/táctil, ejecutado en Chrome |
| Perfiles | Administración, jefatura, coordinación, integrante y consulta/auditoría |

La paginación, la búsqueda superior, el calendario Gantt y el fallo de acceso por `localhost` se reprodujeron también en el servidor original. Las pruebas de creación, edición, validación, cierre, importación y administración se ejecutaron en la copia.

**Conservación:** la comparación de contenido y SHA-256 de 41 tablas de negocio y control de la base original no encontró cambios. Las sesiones e intentos de acceso se excluyeron de esa comparación porque iniciar sesión genera registros técnicos. No se modificó el código de la aplicación. Los servicios auxiliares de auditoría se detuvieron al finalizar.

## Cobertura

Se recorrieron los 11 módulos y las 39 subsecciones de tablas visibles para administración. Se abrieron formularios de alta y se comprobó la validación de campos obligatorios en los 30 recursos que permiten creación. También se abrieron fichas y formularios de edición de registros disponibles. Las secciones vacías se distinguieron de los fallos de funcionamiento.

| Módulo | Secciones y operaciones comprobadas | Resultado relevante |
|---|---|---|
| Acceso | Ruta protegida, campos vacíos, contraseña incorrecta, mostrar/ocultar contraseña, login, logout y acceso posterior sin sesión | Funciona en `127.0.0.1`; problemas de ancho móvil y acceso por `localhost` |
| Dashboard | Tarjetas, filtros, proyectos por clic y teclado, próximos plazos, enlace a acuerdos y reportes | Los enlaces probados llegan al módulo correspondiente |
| Proyectos y Roadmap | Proyectos, hitos, ejes, procesos, dependencias; fichas, formularios, búsqueda y Gantt | Paginación incorrecta; fechas desplazadas en el Gantt |
| Tareas | Tareas, asignaciones, avances y comentarios, cierres; cinco vistas de alcance, lista/Kanban, directorio de participantes | Flujo compartido y cierre funcionales; falla la búsqueda superior sobre la misma ruta |
| Registro Digital | Documentos, versiones, documentos de tareas y tipos; Todos, Emitidos, Recibidos, Normativos/técnicos y Archivo | Secciones y envío funcionan; envío mantiene aprobación pendiente |
| Trámites | Expedientes, historial y actuaciones hasta revisión, firma, derivación y aprobación con resolución | La aprobación actualiza el documento relacionado |
| Reuniones y acuerdos | Reuniones, acuerdos y asistentes; creación de reunión/acuerdo, tarea derivada y cumplimiento | Flujo funcional; el rango de fechas omite reuniones del día final |
| Evidencias | Evidencias, versiones, vínculos y validaciones; alta, versión, validación, duplicado y navegación hacia documento relacionado | Validación, rechazo de duplicado y enlaces internos funcionan |
| Entregables OS | Entregables, órdenes y revisiones; falta de presentación, vínculo a presentación, observación y conformidad | Rechaza revisar sin documento; funciona al completar el requisito |
| Indicadores y calidad | Indicadores, metas/resultados, modelos, criterios, periodos y mejoras; fuente de modelo, validación y resultado 101 % | Los controles de fuente y porcentajes funcionan |
| Reportes y alertas | Mi espacio/Equipo, 7/30 días, seis CSV, dos CSV de vencidos, campana y navegación desde alertas | Descargas y navegación funcionales |
| Administración | Usuarios, roles de usuarios, roles, permisos de roles, permisos, bitácora, importaciones y procedencia; importación CSV/XLSX y protección de la propia cuenta | Paginación bloquea parte de los registros; Exportar en Importaciones devuelve 403 |

### Flujos completos comprobados

- Tarea para dos personas → edición → avances propios con evidencia → revisión → 50 % consolidado cuando solo una persona completó su aporte → 100 % cuando ambas fueron validadas → cierre por jefatura. No se ofreció cierre antes de completar ambos aportes.
- Documento remitido con aprobación pendiente → actuaciones del expediente → firma → derivación → aprobación con documento de resolución → documento aprobado.
- Documento vinculado a tarea → avance al 100 % con evidencia → revisión → cierre seleccionando una versión de evidencia validada, sin usar una justificación de excepción.
- Reunión → acuerdo → tarea derivada → apertura repetida de la misma tarea → avance y cierre → acuerdo cumplido.
- Evidencia → versión → validación → rechazo de versión duplicada → vínculo a documento → navegación entre ambos registros.
- Entregable → documento de presentación → revisión observada → conformidad.
- CSV → lectura de encabezados → mapeo de referencias → previsualización con una fila válida y cero errores → confirmación → un registro importado en la copia. También se leyó una fuente XLSX de prueba.

### Permisos observados

| Perfil | Crear tareas | Vista Equipo | Revisar/cerrar tarea | Administración observada |
|---|---|---|---|---|
| Administrador | Sí | Sí | Sí | Secciones completas |
| Jefatura | Sí | Sí | Sí | Bitácora |
| Coordinación | Sí | No | No | Bitácora |
| Integrante | Sí | No | No | Redirige al Dashboard |
| Consulta/auditoría | No | Sí | No | Bitácora |

El integrante de la tarea compartida no recibió botones para revisar avances ni editar esa tarea creada por otra persona. Se rechazaron la desactivación de la propia cuenta y la retirada del propio rol administrador. Estas comprobaciones no sustituyen una auditoría de seguridad exhaustiva.

## Hallazgos

La prioridad **alta** identifica una función que impide administrar o consultar parte de los registros. **Media** corresponde a resultados incorrectos o funciones que fallan bajo condiciones reproducibles. **Baja** corresponde a problemas de presentación y comprensión que conservan la operación subyacente.

| ID | Prioridad | Problema |
|---|---|---|
| H01 | Alta | Paginación desincronizada: aparecen filas pero el contador indica `1–0 de 0` |
| H02 | Media | La búsqueda superior no filtra cuando el usuario ya está en Tareas |
| H03 | Media | El límite final de un rango de fechas excluye reuniones de ese día |
| H04 | Media | El login requiere 438 px y desborda pantallas de 320–390 px |
| H05 | Media | La búsqueda visible se ignora en varias relaciones e historiales |
| H06 | Media | Validaciones de acciones/importación muestran rutas técnicas, inglés y JSON |
| H07 | Baja | Varias tablas muestran nombres internos de campos |
| H08 | Media | El Gantt desplaza fechas un día hacia atrás en America/Lima |
| H09 | Media | Fechas de actualización UTC sin zona se muestran como si fueran locales |
| H10 | Media | El botón Exportar de Importaciones siempre recibe HTTP 403 |
| H11 | Media | El acceso desde `localhost` vuelve al login con credenciales correctas |
| H12 | Baja | Hashes y rutas largas se superponen con columnas de Importaciones |

### H01 — Paginación desincronizada

**Reproducción:** iniciar como administrador, abrir Administración → Usuarios y observar el pie de tabla. Cambiar el tamaño de página a 100.

**Resultado real:** la API devuelve `total: 35` e inicialmente 20 elementos. La tabla muestra 20 usuarios, pero indica `1–0 de 0` y no ofrece una navegación útil a la página siguiente. Al elegir 100, se ven los 35 usuarios, pero el selector sigue mostrando 20 y el contador sigue en cero. El mismo patrón aparece en otras tablas. Permisos de roles contiene 119 registros; aumentar a 100 no permite consultar los restantes mediante una paginación correcta.

**Esperado:** contador, tamaño seleccionado, botones y filas deben representar el mismo estado. Con 35 usuarios y tamaño 20 debe mostrarse un rango equivalente a `1–20 de 35` y permitir pasar al resto.

**Impacto:** registros fuera de la primera página resultan inaccesibles por el recorrido normal. Es especialmente relevante para usuarios, permisos y bitácora.

**Mejora necesaria:** revisar la sincronización de la paginación entre `ModuleView.vue` y `EntityTable.vue`, incluyendo `rowsNumber`, tamaño de página y eventos de Quasar. Comprobar después conjuntos de más de 20 y más de 100 registros.

**Evidencia:** `deep-results.json`, caso `confirmed-pagination-users`; `original-pagination-proof.png`; `final-results.json`, exportación de permisos de roles.

### H02 — La búsqueda superior no se aplica sobre Tareas

**Reproducción:** abrir Tareas, seleccionar Equipo, escribir `ZZZ_NO_EXISTE_AUDIT` en la barra superior y pulsar Enter.

**Resultado real:** la URL pasa a `/tareas?q=ZZZ_NO_EXISTE_AUDIT`, pero el buscador de la tabla permanece vacío y las filas siguen siendo exactamente las mismas. Si se hace la misma búsqueda desde Proyectos, se entra a Tareas con el texto correctamente aplicado y cero resultados.

**Esperado:** cambiar la consulta debe actualizar el filtro aunque la ruta ya sea `/tareas`.

**Impacto:** el usuario puede interpretar que los resultados corresponden a su búsqueda cuando el listado no cambió.

**Mejora necesaria:** sincronizar `route.query.q` con los filtros del módulo también al cambiar la consulta sobre la misma ruta. El observador de consultas de `ModuleView.vue` actualmente contempla alcance, recurso e identificador, pero no actualiza la búsqueda.

**Evidencia:** `deep-results.json`, caso `confirmed-global-search`; `original-global-search-proof.png`.

### H03 — El rango omite reuniones del último día

**Reproducción:** crear una reunión para el 14/10/2026 a las 10:00, buscarla y aplicar Desde 14/10/2026 y Hasta 14/10/2026.

**Resultado real:** la reunión aparece antes del rango y desaparece al aplicarlo: de una fila a cero.

**Esperado:** un rango que incluye el 14 de octubre debe incluir las reuniones de ese día, cualquiera que sea su hora.

**Impacto:** consultas diarias y rangos que terminan en una fecha pueden omitir reuniones válidas.

**Mejora necesaria:** tratar el límite superior de campos con hora como el inicio del día siguiente de forma exclusiva, o incluir todo el día final. Revisar `filtered()` en `backend/app/service.py`; el límite actual compara directamente con una fecha sin hora. Conservar el comportamiento apropiado para campos que solo almacenan una fecha.

**Evidencia:** `extra-results.json`, caso `meeting-date-range-boundary`; `confirmed-meeting-date-range.png`.

### H04 — Login con desbordamiento horizontal móvil

**Reproducción:** abrir el login con anchos 320, 375 y 390 px.

| Viewport | Ancho del documento | Desbordamiento |
|---|---|---|
| 320 px | 438 px | 118 px |
| 375 px | 438 px | 63 px |
| 390 px | 438 px | 48 px |
| 768 px | 768 px | 0 px |
| 1440 px | 1440 px | 0 px |

**Resultado real:** el formulario mantiene un ancho que excede el espacio disponible. En emulación móvil también se observó una ampliación del ancho de disposición a 438 px, frente al viewport configurado de 390 px.

**Esperado:** el login debe caber dentro de la pantalla sin desplazamiento horizontal ni reducción automática del contenido.

**Mejora necesaria:** revisar el ancho de `.login-form-inner`, el mínimo intrínseco de la cuadrícula y el padding de `.login-form` en `frontend/src/style.css`. Verificar con el ancho del viewport/documento, además de `innerWidth`, para detectar la ampliación que realizan los navegadores móviles.

**Evidencia:** `extra-results.json`, caso `login-layout-widths`; `login-layout-320.png`, `login-layout-390.png`.

### H05 — Búsquedas ofrecidas que no filtran

**Reproducción:** en una sección con registros de la siguiente tabla, escribir `ZZZ_NO_EXISTE_AUDIT` en Buscar por nombre o número y esperar a que se complete la petición.

| Sección | Filas antes | Filas después |
|---|---|---|
| Asignaciones | 1 | 1 |
| Historial de trámites | 1 | 1 |
| Asistentes | 3 | 3 |
| Metas y resultados | 1 | 1 |
| Roles de usuarios | 20 | 20 |
| Permisos de roles | 20 | 20 |
| Bitácora de auditoría | 20 | 20 |
| Importaciones | 2 | 2 |

**Resultado real:** se envía el filtro `q`, pero los registros no cambian, aunque el texto no existe. La búsqueda sí filtra en las tablas principales de proyectos, tareas, documentos, reuniones y otras entidades con campos compatibles.

**Esperado:** ofrecer búsqueda por los textos que aparecen en la sección, o retirar ese control cuando no se admite.

**Mejora necesaria:** ampliar la búsqueda del backend a comentarios, notas, archivos, acciones y etiquetas de relaciones según cada recurso. La implementación actual de `filtered()` solo considera un grupo fijo de campos como título, nombre, número y correo. Evitar mostrar un filtro sin efecto.

**Evidencia:** casos `confirmed-resource-*` de `deep-results.json`. Las secciones inicialmente vacías no se utilizaron para concluir que la búsqueda fallaba.

### H06 — Mensajes de validación poco utilizables

**Reproducción A:** abrir Registrar mi avance y confirmar sin comentario ni evidencia.<br>
**Resultado:** `body.comment: Field required`, `body.evidence.title: Field required` y `body.evidence.url: Field required`.

**Reproducción B:** previsualizar un CSV de documentos con solo número y título.<br>
**Resultado:** se presenta una lista JSON extensa con claves `type`, `loc`, `msg`, `input` y enlaces de errores de Pydantic.

**Esperado:** mensajes en español asociados a los campos visibles, por ejemplo “Ingresa un comentario” y “Adjunta el enlace de la evidencia”. Para importación, indicar fila, columna y corrección necesaria.

**Impacto:** los controles del backend protegen los datos, pero su presentación dificulta que la persona corrija el formulario. Los campos requeridos de estas acciones tampoco se identifican con la misma claridad que en los formularios generales.

**Mejora necesaria:** traducir y mapear errores de API a etiquetas de la interfaz; añadir validación previa y marcas de campos obligatorios en las acciones. Sustituir el JSON de importación por una tabla de errores comprensible, conservando el detalle técnico para diagnóstico.

**Evidencia:** `deep-results.json`, casos `task-invalid-advance` e `import-file-errors`; `invalid-action-43.png` y `import-csv-validation.png`. El archivo JSON identifica el caso si cambia el índice de la captura.

### H07 — Nombres internos en tablas

**Resultado observado:** algunas cabeceras muestran `author_id`, `comment`, `case_id`, `approver_id`, `evidence_version_id`, `validator_id`, `reviewer_id`, `entity`, `actor_id`, `filename`, `backup_path`, `batch_id` y `record_id`.

**Esperado:** etiquetas como Autor, Comentario, Expediente, Aprobador, Versión de evidencia, Revisor, Entidad, Usuario y Archivo. También se encontró `Version` sin la etiqueta localizada habitual.

**Impacto:** las pantallas de historial, revisión, cierre y administración resultan menos claras para usuarios sin conocimientos técnicos.

**Mejora necesaria:** completar las etiquetas de metadatos en `backend/app/catalog.py` y las alternativas de presentación de tablas/fichas. Aplicar la misma terminología a formularios, columnas y CSV cuando corresponda.

**Evidencia:** encabezados registrados en `deep-results.json`; capturas de las secciones confirmadas y `export-unavailable-imports.png`.

### H08 — Fechas incorrectas en el eje del Gantt

**Reproducción:** en el servidor original, iniciar con administración y abrir Proyectos → Vista Gantt, usando America/Lima.

**Resultado real:** las dos actividades recibidas tienen inicio y plazo `2026-10-13`, pero el eje muestra `12 oct`, `12 oct`, y después cinco etiquetas `13 oct`. El problema también aparece en rangos más amplios de la copia.

**Esperado:** una fecha de inicio del 13 de octubre debe representarse como 13 de octubre. Las marcas del eje deben adaptarse a la longitud del rango para evitar repetir fechas de forma confusa.

**Mejora necesaria:** manejar las fechas sin hora como fechas de calendario, evitando interpretarlas como medianoche UTC y luego formatearlas en la zona local. Revisar `Date.parse()` y las marcas de `GanttChart.vue`.

**Evidencia:** `final-results.json`, caso `original-gantt-dates-confirmed`; `original-gantt-date-proof.png`.

### H09 — La fecha de actualización se adelanta un día

**Resultado reproducido:** durante la prueba, la fecha local era **13/10/2026**. La API devolvió `2026-10-14T02:50:10.932924`, sin indicador de zona, y la ficha mostró **Actualizado 14 oct. 2026**. Interpretado como UTC, ese instante corresponde al **13/10/2026** en Lima.

**Esperado:** representar la fecha local correspondiente al instante real de actualización.

**Impacto:** las fichas y la trazabilidad pueden presentar una fecha futura o incorrecta cerca del cambio de día.

**Mejora necesaria:** serializar los instantes UTC con zona explícita y convertirlos de forma consistente a la zona de presentación. `models.now()` genera UTC y elimina la información de zona; el navegador interpreta el texto recibido como hora local. Separar este tratamiento de los campos de calendario que no tienen hora.

**Evidencia:** `final-results.json`, caso `timestamp-timezone-confirmed`; `timestamp-timezone-proof.png`.

### H10 — Exportar en Importaciones no está disponible

**Reproducción:** iniciar como administrador, abrir Administración → Importaciones y pulsar Exportar.

**Resultado real:** la solicitud a `/api/reports/import-batches.csv` recibe HTTP 403 con “Exportación no disponible para este recurso”. No se produce una descarga. El botón permanece ofrecido.

**Esperado:** exportar cuando se ofrece la acción, o presentar claramente su indisponibilidad antes de pulsarla.

**Mejora necesaria:** decidir si se implementará esa exportación o se ocultará/deshabilitará el control para el recurso. La restricción del backend es explícita; no debe eliminarse indiscriminadamente como una corrección de permisos.

**Evidencia:** `final-results.json`, caso `export-module-/administracion-Importaciones`; `export-unavailable-imports.png`. Los otros 38 recursos de tablas sí generaron CSV UTF-8 con BOM.

### H11 — Login fallido mediante localhost

**Reproducción:** abrir `http://localhost:5173/login` e iniciar con credenciales válidas. Repetir con `http://127.0.0.1:5173/login`.

**Resultado real:** usando localhost, la aplicación vuelve al login y muestra “Inicia sesión para continuar”. Usando 127.0.0.1, la sesión y la navegación funcionan. Se reprodujo también en la copia 5174/8001: el login es seguido por respuestas 401 en recursos protegidos.

**Esperado:** que las direcciones locales admitidas funcionen de manera coherente, o que la aplicación conduzca al host local configurado.

**Área a revisar:** el frontend usa por defecto la API en `127.0.0.1`, mientras que la página está en `localhost`. La configuración admite ambos orígenes, pero son sitios distintos para el tratamiento de cookies. Revisar conjuntamente URL de API, host de acceso y política de cookies; verificar la hipótesis con la red/cookies del navegador al corregirlo.

**Alternativa actual comprobada:** entrar mediante `http://127.0.0.1:5173`.

**Evidencia:** `final-results.json`, caso `localhost-login-behavior`; `closing-results.json`, caso `localhost-original-login-confirmed`; `original-localhost-login-proof.png`.

### H12 — Superposición de texto en Importaciones

**Reproducción:** abrir Administración → Importaciones en escritorio, con los lotes de catálogo y participantes ya existentes.

**Resultado observado:** cadenas largas de SHA-256 y nombres de respaldo exceden sus columnas y se superponen con el texto de hoja y entidad. La tabla pierde legibilidad incluso a 1440 px de ancho.

**Esperado:** que valores largos no invadan las celdas vecinas.

**Mejora necesaria:** permitir cortes seguros de texto largo, limitar su presentación con acceso al valor completo, o utilizar una ficha para los detalles del hash y respaldo. Conservar los valores íntegros para trazabilidad y copia.

**Evidencia visual:** `export-unavailable-imports.png`, que también muestra los lotes anteriores a las pruebas.

## Visualización y mejoras adicionales

Fuera del login, los módulos probados se adaptaron a los anchos estrechos sin desbordamiento global de página. El menú móvil abrió, permitió navegar y se cerró después de seleccionar un módulo. El formulario móvil permitió seleccionar temática, completar campos y guardar una tarea con HTTP 201. La selección de todo el equipo mostró 34 personas disponibles y se canceló sin crear esa tarea grupal.

Las tablas y pestañas usan desplazamiento horizontal propio. En la emulación de 390 px, la tabla de Tareas tenía 846 px de contenido en un contenedor de 356 px; las pestañas de Administración tenían 785 px en el mismo ancho disponible. Se comprobó que desplazarlas permite llegar a Origen de registros y al botón Abrir detalle. **Ese desplazamiento funciona**, pero sería más fácil descubrirlo con una indicación visual o una vista móvil por tarjetas.

Otras mejoras útiles:

- Mostrar el alcance activo del Gantt y ofrecer Mi espacio/Equipo para perfiles autorizados, como ya sucede en Tareas, Dashboard y Reportes.
- Ajustar las marcas del Gantt a rangos cortos y largos, además de corregir su fecha inicial.
- Añadir regresiones de navegador para paginación real, consultas sobre la misma ruta, límites diarios, login móvil y zona horaria. Las comprobaciones DOM existentes no detectaron los problemas reproducidos aquí.

## Consola, red y estados de error

No se registraron excepciones JavaScript `pageerror` en los recorridos. Esto no significa que la aplicación esté libre de defectos: varios problemas producen resultados incorrectos sin romper la ejecución.

Las respuestas 401 antes de iniciar sesión o después de cerrarla fueron esperadas. También fueron esperados los rechazos por campos incompletos, versión duplicada, porcentaje fuera de rango, revisión sin documento, validación de modelo sin fuente y protección de la propia cuenta.

Los fallos relevantes de red fueron el HTTP 403 del botón de exportación de Importaciones y los HTTP 401 posteriores al login por localhost. Se provocó un HTTP 503 controlado en Proyectos para comprobar el estado de error: la pantalla presentó Reintentar y recuperó los cuatro proyectos disponibles en esa fase al retirar la simulación. Ese 503 fue una prueba de recuperación, no una caída espontánea del servidor.

Las primeras ejecuciones de automatización necesitaron corregir selectores de pestañas, filas relacionadas y menús móviles. Esos intentos fallidos no se contaron como errores de la aplicación. Las pruebas posteriores confirmaron esas funciones en el navegador.

## Orden recomendado de corrección

1. **H01:** paginación y acceso a todos los registros, incluyendo conjuntos superiores a 100.
2. **H02 y H05:** consistencia de búsquedas y consultas sobre la misma ruta.
3. **H03, H08 y H09:** fechas, límites de rango y zona horaria.
4. **H04 y H11:** acceso móvil y coherencia del host local.
5. **H06, H07, H10 y H12:** validaciones comprensibles, etiquetas, disponibilidad de exportación y legibilidad de tablas.

Para aceptar las correcciones deben repetirse las reproducciones indicadas, verificar el resultado esperado y comprobar que los flujos de tareas, evidencias, trámites e importación siguen funcionando. Esta auditoría no aplicó esas correcciones.

## Evidencias y límites

Las capturas, descargas, fixtures y registros están en `.local/browser-audit/`. Las herramientas están en `.local/audit-tools/`; ambas carpetas están ignoradas por Git.

Registros de ejecución:

- `initial-events.json`: acceso inicial al servidor original.
- `results.json`: recorrido inicial de módulos, fichas, vistas, reportes y tamaños de pantalla.
- `deep-results.json`: comprobaciones estables de las 39 secciones, 30 formularios, perfiles y flujo compartido.
- `extra-results.json`: límites de fecha, evidencias, reunión/acuerdo, importación y formularios móviles.
- `final-results.json`: enlaces, fechas, exportaciones de los 39 recursos y acceso por localhost.
- `closing-results.json`: aprobación documental, cierre con evidencia, protección del rol propio y localhost original.
- `original-integrity.json`: comparación final de las 41 tablas, sin cambios.

Capturas principales:

- [Paginación en el servidor original](<C:/Users/yaque/Documents/TASK PAGINA WEB/.local/browser-audit/original-pagination-proof.png>)
- [Búsqueda superior sin efecto](<C:/Users/yaque/Documents/TASK PAGINA WEB/.local/browser-audit/original-global-search-proof.png>)
- [Gantt con fechas desplazadas](<C:/Users/yaque/Documents/TASK PAGINA WEB/.local/browser-audit/original-gantt-date-proof.png>)
- [Login de 320 px con documento de 438 px](<C:/Users/yaque/Documents/TASK PAGINA WEB/.local/browser-audit/login-layout-320.png>)
- [Exportación rechazada y texto superpuesto](<C:/Users/yaque/Documents/TASK PAGINA WEB/.local/browser-audit/export-unavailable-imports.png>)
- [Tarea cerrada con evidencia validada](<C:/Users/yaque/Documents/TASK PAGINA WEB/.local/browser-audit/task-closed-with-evidence.png>)

**Límites:** se comprobó Chrome con emulación móvil; no se ejecutaron Safari, Firefox ni dispositivos físicos. No se verificaron Supabase/PostgreSQL, despliegues públicos, SSO institucional ni los permisos reales de Google Drive. Los enlaces de evidencia creados para la auditoría eran ficticios en la copia; se comprobó su apertura como enlace HTTPS, no la existencia de un documento institucional. La previsualización XLSX se probó con una fuente pequeña de auditoría, no con todas las variantes del libro institucional. Tampoco se realizaron pruebas de carga, concurrencia masiva ni una certificación de accesibilidad.

La revisión cubre las rutas, secciones y flujos indicados; no afirma haber probado todas las combinaciones posibles de datos y permisos.
