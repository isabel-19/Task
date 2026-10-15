# TASK.md — SISTEMA ROADMAP OGC (UNAJMA)

## 1. ¿Qué proyecto se desarrollará?
**ROADMAP OGC** es una aplicación web interna de la **Oficina de Gestión de la Calidad (OGC) de la Universidad Nacional José María Arguedas (UNAJMA)**. Permitirá planificar actividades institucionales, distribuir tareas entre integrantes, controlar plazos y avances, registrar reuniones y acuerdos, gestionar cartas e informes, hacer seguimiento a trámites y aprobaciones, y conservar evidencias verificables.

**Resultado esperado:** una sola plataforma conectada, no once páginas independientes. Ejemplo: *documento recibido → tarea asignada → informe/carta elaborada → trámite o derivación → evidencia → validación/cierre*. Otro ejemplo: *reunión → acuerdo → tarea → avance → evidencia → cierre*.

**Tecnologías:** Vue 3 + Quasar (frontend), Python + FastAPI (backend), PostgreSQL de Supabase (base de datos), GitHub (código), Cloudflare Pages (frontend), Render (backend, entorno de prueba), Google Drive institucional (archivos mediante enlaces autorizados). Primero construir y probar localmente. Los planes gratuitos son para prototipo/pruebas, no para producción institucional sin evaluación de seguridad y continuidad.

## 2. Módulos obligatorios y funciones

1. **Dashboard:** pendientes, tareas vencidas, próximas entregas, acuerdos sin cumplir, documentos pendientes, progreso por responsable, eje temático y periodo; filtros y acceso al detalle.
2. **Proyectos y Roadmap:** ejes y proyectos OGC, cronograma Gantt, actividades, hitos, dependencias, fechas, responsables, estados y avance consolidado.
3. **Tareas y responsables:** mis tareas/todas las tareas, asignación individual o grupal, prioridad, plazos, subtareas, tareas recurrentes, Kanban, historial de avances, observaciones, revisión y cierre con evidencias.
4. **Registro Digital:** registro único de **cartas, cartas múltiples, informes, informes técnicos, memorandos, oficios, documentos recibidos, directivas, planes, reglamentos, manuales y otros**; número, año, fecha, asunto, emisor, destinatario, responsable, documento de referencia, archivo/enlace, versión y búsqueda. Secciones: emitidos, recibidos, normativos/técnicos y archivo digital. Un documento puede vincularse con tareas, proyectos, reuniones y expedientes sin duplicarlo.
5. **Seguimiento de trámites:** estados de elaboración, revisión, firma, derivación, observado, subsanación, aprobado/atendido; dependencia actual, fechas, última actuación, expediente, resoluciones, observaciones e historial. **Documento enviado no equivale a documento aprobado.**
6. **Reuniones, actas y acuerdos:** participantes, fecha, agenda, actas, acuerdos, responsables, compromisos, vencimientos, evidencias; generar tareas desde acuerdos y consultar su cumplimiento en la próxima reunión.
7. **Evidencias y medios de verificación:** archivos/enlaces Drive con nombre, categoría, fecha, versión, autor, validación y relación a tareas, documentos, acuerdos, proyectos e indicadores; solicitud y seguimiento de evidencias a otras áreas.
8. **Entregables de órdenes de servicio (OS):** OS, SIAF cuando aplique, prestador/responsable, entregable, plazo, documento de presentación, revisión, observaciones, conformidad y estado. Es seguimiento interno, no reemplaza SIGA/SIAF.
9. **Indicadores y modelos de calidad:** CBC aplicables, ISO 21001, ISO 9001, ICACIT, ACBSP, CIEES, SINEACE y otros; estándares/criterios/indicadores, metas, resultados, periodos, responsables, evidencias y planes de mejora. No precargar criterios obsoletos como vigentes sin validación.
10. **Reportes y alertas:** reportes semanales/mensuales por integrante y eje, documentos emitidos/recibidos, acuerdos pendientes, OS, tareas vencidas; exportaciones y notificaciones de fechas próximas.
11. **Administración:** usuarios, perfiles, roles (jefatura, coordinador, integrante, consulta/auditoría, administrador), permisos por acción, catálogos, tipos de documento, configuraciones y bitácora de auditoría.

## 3. Reglas funcionales transversales
- **Registro único y relaciones:** evitar duplicar documentos, tareas y acuerdos cuando aparecen en varios módulos.
- Cada registro tiene identificador, fecha de creación/modificación y usuario que lo modificó.
- Distinguir **responsable OGC** de **dependencia externa** encargada de revisar/aprobar un trámite.
- Una tarea requiere estado, responsable, fecha y progreso; su cierre necesita evidencia validada o justificación autorizada.
- Los documentos emitidos controlan preparación y envío digital, físico o ambos, según las listas del Excel; las cartas emitidas no se aprueban. La aprobación/atención corresponde al seguimiento de documentos recibidos y expedientes.
- Filtrar por año, mes, eje, proceso, responsable, tipo, estado y plazos; permitir búsqueda de texto.
- Adjuntar enlaces/archivos con permisos adecuados; no exponer documentos internos en URLs públicas.
- No usar datos institucionales reales en entornos de prueba ni guardar credenciales en Git.

## 4. Fuentes para futura importación
- **ROADMAP OGC 2026 v2**: hojas de Gantt, meses, TASK, PAINS, Roles, Entregables OS, Consultas/medios de verificación, REGISTRO DIGITAL y demás hojas pertinentes.
- **Registro de documentos internos** (Excel compartido): columnas como N.° documento, eje, tipo, nombre, elaborado, revisado, aprobado/atendido, aprobador, referencia, fecha de envío, plazo, comentarios y enlace de resolución.
- **Archivos Excel enlazados dentro de REGISTRO DIGITAL:** identificarlos y revisarlos antes de definir la importación definitiva. **No asumir que ya están leídos o importados.**
- Normalizar, mapear encabezados, identificar duplicados, guardar archivo/hoja/fila de origen y hacer copia de seguridad. **No modificar los archivos originales durante la importación.**

## 5. Instrucciones para el agente de desarrollo
1. Lee este TASK.md completo **antes de escribir código** y úsalo como especificación de alcance.
2. Trabaja en orden, en la **primera casilla [ ]** sin dependencias pendientes; al verificarla cámbiala a **[x]**.
3. Registra en la Bitácora qué se implementó, cómo se probó y cuál es el siguiente paso. Continúa con el siguiente pendiente sin esperar otra instrucción mientras sea posible.
4. Si hay bloqueos de credenciales, decisiones institucionales, permisos o acciones irreversibles, documéntalos y sigue solo con tareas independientes. Nunca inventes accesos.
5. No marques como terminado algo sin implementación funcional y prueba. No simules datos como si fueran reales.
6. Mantén código y esquema documentados, componentes reutilizables y relaciones coherentes con los 11 módulos.

## 6. Lista de tareas de desarrollo

### Fase 1 — Fundamentos
- [x] Crear monorepositorio con `frontend/`, `backend/`, `database/`, `docs/`, `TASK.md`, `.gitignore` y `.env.example`.
- [x] Inicializar Vue 3 + Quasar y FastAPI; documentar ejecución local en README.
- [x] Definir mapa de navegación de los **11 módulos**, rutas y roles de acceso.
- [x] Crear esquema de entidades y diagrama de relaciones en `docs/modelo-datos.md` basado en la sección 2.

### Fase 2 — Base de datos (PostgreSQL / Supabase)

**Verificación local:** entidades y controles probados con SQLite y claves foráneas activas; SQL PostgreSQL compilado en esquema privado `roadmap`. No se ha ejecutado la migración en PostgreSQL/Supabase. Esa comprobación permanece pendiente en la última casilla de esta fase y en la configuración de PostgreSQL de la fase 4.
- [x] Crear usuarios, perfiles, roles, permisos y asignaciones de roles.
- [x] Crear ejes temáticos, procesos, proyectos, hitos y dependencias.
- [x] Crear tareas, asignaciones, subtareas, avances, comentarios, observaciones y aprobaciones de cierre.
- [x] Crear tipos documentales, documentos (emitidos/recibidos/normativos), relaciones entre documentos y versiones.
- [x] Crear expedientes, etapas, derivaciones, observaciones, aprobaciones y resoluciones; vincularlos a documentos.
- [x] Crear reuniones, asistentes, actas, acuerdos, tareas derivadas y seguimiento de compromisos.
- [x] Crear evidencias, versiones, validaciones y relaciones con tareas/documentos/reuniones/indicadores.
- [x] Crear órdenes de servicio, entregables, plazos, presentaciones y conformidades.
- [x] Crear modelos de calidad, criterios, indicadores, periodos, metas, resultados y planes de mejora.
- [x] Agregar llaves foráneas, índices, restricciones únicas, timestamps y auditoría de cambios.
- [ ] Escribir migraciones SQL reproducibles y datos **ficticios** para desarrollo; probar relaciones.

### Fase 3 — Frontend base (Vue 3 + Quasar)
- [x] Crear layout responsive institucional con encabezado, menú lateral de 11 módulos y navegación.
- [x] Crear login, sesión, permisos y rutas protegidas (sin confiar solo en el frontend).
- [x] Construir componentes comunes: tablas, filtros, formularios, modales, estados, buscador y selector de evidencias.
- [x] Crear pantallas base y rutas funcionales para cada módulo, incluyendo vacíos/carga/error.

### Fase 4 — Backend / API (FastAPI)
- [ ] Configurar PostgreSQL, ORM, validaciones, migraciones, manejo de errores y variables de entorno.
- [x] Implementar autenticación y autorización por acción en API.
- [x] Crear API para proyectos, cronograma, tareas, asignaciones, avances y cierre.
- [x] Crear API para Registro Digital y vínculos entre documentos, tareas y proyectos.
- [x] Crear API para trámites, derivaciones, observaciones, aprobaciones y resoluciones.
- [x] Crear API para reuniones, actas, acuerdos y creación de tareas desde acuerdos.
- [x] Crear API para evidencias, OS/entregables, indicadores y modelos de calidad.
- [x] Crear API del dashboard, reportes, alertas y registros de auditoría.
- [x] Implementar búsqueda, filtros, paginación y controles contra duplicados.

### Fase 5 — Implementación de los 11 módulos en pantalla

**Verificación:** compilación de producción, pruebas de componentes y las 11 pantallas con el contrato de la API local. La inspección visual y la prueba de navegador institucional están pendientes y no se sustituyen por los tests DOM.
- [x] Dashboard con contadores y filtros alimentados por API.
- [x] Proyectos y Roadmap con listado, detalle e interfaz Gantt.
- [x] Tareas con Mis tareas, Todas, Kanban, detalle, comentarios, progreso y validación.
- [x] **Registro Digital** con cuatro secciones, alta/edición/búsqueda de documentos y relaciones.
- [x] Trámite documental con historial de etapas, derivados, observaciones y resolución.
- [x] Reuniones con agenda, asistentes, acta, acuerdos y seguimiento.
- [x] Evidencias y medios de verificación con enlaces y validación.
- [x] Entregables OS con plazos, documentos de presentación y conformidad.
- [x] Indicadores y modelos de calidad con metas, periodos y medios de verificación.
- [x] Reportes y alertas con exportación y filtros.
- [x] Administración de usuarios, roles y catálogos.

### Fase 6 — Integración e importación
- [x] Probar flujo documento recibido → tarea → carta/informe → trámite → evidencia → cierre.
- [x] Probar flujo reunión → acuerdo → tarea → evidencia → cierre.
- [x] Probar permisos, historial, trazabilidad, búsquedas, plazos y prevención de duplicados.
- [x] Documentar mapeo de hojas del ROADMAP y registro documental a tablas nuevas.
- [ ] Identificar Excel enlazados en REGISTRO DIGITAL y añadir al mapeo tras revisarlos.
- [x] Implementar importador con previsualización, validación, respaldo y reporte de errores; sin alterar fuentes originales.
- [x] Ejecutar pruebas automatizadas de API y componentes principales.

### Fase 7 — Publicación de prueba y entrega
- [ ] Publicar frontend y backend juntos en Render Free con Supabase Free, por elección del usuario del 15 de octubre.
- [ ] Configurar Supabase, seguridad, variables de entorno y permisos mínimos.
- [ ] Verificar funcionamiento de extremo a extremo con datos ficticios.
- [x] Documentar backups, restauración y límites de hosting gratuito.
- [x] Crear manual breve de uso y administración y checklist previo a producción institucional.

## Criterio de cierre
Una casilla solo se marca `[x]` cuando su código/documentación existe y se verificó. Nunca desplegar información institucional real en la infraestructura gratuita sin autorización y revisión de seguridad.

## Bitácora de avance
| Fecha | Tarea | Resultado / prueba | Próximo paso o bloqueo |
|---|---|---|---|
| 2026-10-15 | Render gratuito elegido por el usuario | Blueprint Free con interfaz/API en un contenedor; archivos privados en Supabase Storage sin disco efímero, control de sesión/tarea antes de leer, integridad y compensación si falla la transacción. Migración al arranque y alta inicial sin shell. Suite de 100 pruebas correcta y dos comprobaciones adicionales de arranque correctas | Render con sesión iniciada; faltan accesos GitHub/Supabase, push actualizado, PostgreSQL y prueba real de persistencia. Todavía no hay URL publicada; no se crearon recursos de pago |
| 2026-10-15 | Preparación de publicación solicitada | Contenedor con interfaz y API juntas, exclusión de secretos/datos locales, alternativa Render con disco privado y alta inicial de jefatura sin demo. Tres pruebas nuevas, build, prueba integrada de interfaz compilada/API y diff correctos. Ningún recurso de pago creado ni dato local transferido | Pendiente conectar alojamiento/repositorio y elegir servidor institucional, pago o prueba limitada. Docker y PostgreSQL reales sin verificar; todavía no hay URL pública |
| 2026-10-15 | Drive personal y compartido con previsualización previa | Tres vistas del selector, soporte de unidades compartidas, previsualización privada sin crear evidencias y apertura del original cuando el propietario bloquea copias. Fallos del proveedor regresan a Cuentas vinculadas. 92 pruebas backend y 75 frontend, build y conexión OAuth real correctos tras autorizar la salida de red de la API; selector real y pestaña de compartidos abiertos sin errores | Google sigue en modo Prueba y Publicar app está deshabilitado hasta completar la marca. Falta dirección pública/políticas para publicación general y elegir un documento real para comprobar su contenido; no se copiaron documentos reales |
| 2026-10-15 | Registro real de Google autorizado por el propietario | Proyecto de ROADMAP OGC creado; Drive y Picker habilitados; consentimiento preparado y aceptado por el propietario, cliente OAuth web y clave restringida creados con autorización. Configuración central cifrada en la instancia local 5174, respaldo previo, cuenta aportada en usuarios de prueba y permisos openid/email/drive.file declarados. Ningún secreto expuesto en código o documentación | Falta iniciar sesión en ROADMAP y autorizar la vinculación personal para comprobar selección y evidencia reales. Google permanece en modo Prueba; Microsoft y publicación siguen pendientes |
| 2026-10-14 | Configuración central Google/Microsoft y acceso de usuarios autorizados | Panel exclusivo de jefatura/administración, credenciales cifradas y preservadas al dejar sus campos vacíos; aplicación inmediata para todos, conexiones personales y permiso tasks.write para autorizar. Migración 010 respaldada y aplicada sin alterar registros anteriores. 89 pruebas backend, 72 frontend, build y navegador 1440/390/320 px correctos; guardado persistente de jefatura y rechazo 403 al integrante comprobados | Falta registrar las aplicaciones externas y sus credenciales una sola vez para la oficina; no se conectaron cuentas reales. PostgreSQL/publicación pendientes |
| 2026-10-14 | Vinculación Google/Microsoft por usuario para evidencias | Cuentas vinculadas, OAuth con PKCE y estado de un solo uso ligado a sesión, tokens cifrados y renovación; Google Picker y exploración de OneDrive, copia privada con origen y revisión de jefatura. Migración 009 aplicada con respaldo y conservación de registros. 87 pruebas backend y 70 frontend, build y navegador 1440/390/320 px correctos; proveedor remoto simulado en pruebas. Guía en docs/cuentas-google-microsoft.md | Activación real pendiente: no hay client IDs/secrets de Google Cloud y Microsoft Entra configurados; requiere registrar aplicaciones y autorizar cuentas. PostgreSQL/publicación pendientes |
| 2026-10-14 | Evidencias desde el equipo, previsualizador y persona que asignó la tarea | Carga privada PDF/imágenes/DOCX/XLSX/TXT/CSV o enlace; visor y descarga con permisos de tarea, aviso/revisión y cierre conservados. Asignada por visible en lista, móvil, agenda y cabecera de ficha. Migración 008 aplicada con respaldo y conservación de registros. 78 pruebas backend, 60 frontend, build y flujo real de navegador con cinco formatos, observación, corrección y cierre correctos | PostgreSQL y publicación siguen pendientes; archivos requieren almacenamiento persistente y respaldo junto a la base |
| 2026-10-14 | Agenda, apertura visible de evidencias y azul institucional | Botones directos en lista/agenda y Registro Digital; ficha separada por pestañas, envío pendiente y respuesta de jefatura diferenciados, bloqueo de revisión propia y acceso a archivos vinculados anteriores. Agenda semanal con filtros, paginación, Hoy y vencidas. 68 pruebas backend, 51 frontend, build y flujo con dos sesiones en escritorio/móvil correctos. Guía en docs/agenda-evidencias-azul.md | PostgreSQL y despliegue siguen pendientes |
| 2026-10-14 | Jefatura con el mismo nivel de acceso que Administrador, por indicación del usuario | Migración 007 aditiva e idempotente, seed con permisos equivalentes y protección de acceso propio para ambos roles. Pruebas de usuarios, roles, permisos y conservación de cuentas/datos. Guía en docs/jefatura-administracion.md | PostgreSQL y despliegue siguen pendientes |
| 2026-10-14 | Revalidación solicitada por el usuario | 63 backend y 42 frontend correctas; build y diff --check correctos. Navegador con dos sesiones: asignación múltiple → evidencia → aviso automático → persistencia al reiniciar sesión → observación → corrección → nuevo aviso → validación y retirada del pendiente. Sin cambios de código; informe en docs/revalidacion-tareas-2026-10-14.md | PostgreSQL y despliegue permanecen fuera del alcance verificado |
| 2026-10-14 | Avisos de nuevas evidencias a jefatura | Campana y aviso automático, pendientes persistentes por integrante, vista Evidencias por revisar; validación/observación retiran el aviso. 63 pruebas backend, 42 frontend, build y navegador con dos sesiones: evidencia → aviso automático → revisión → pendiente resuelto | PostgreSQL y despliegue siguen pendientes |
| 2026-10-14 | Corrección solicitada: varias personas y evidencia visible para cada destinatario | Selector múltiple, botón Añadir evidencia y formulario dentro de la ficha; cada integrante aporta con su cuenta aunque no pueda editar la asignación ni administrar Evidencias. Filtros incluyen integrantes adicionales. 61 backend, 41 frontend, build y navegador con dos cuentas/dos evidencias; añadir otra persona conservó los aportes | PostgreSQL y despliegue siguen pendientes |
| 2026-10-13 | Fase 1: monorepositorio, Vue/Quasar, FastAPI, rutas, roles y modelo | Build Vite correcto; health API 200; 11 rutas comprobadas en Vitest; 41 tablas compiladas en SQL PostgreSQL/SQLite | Verificar módulos y flujos locales; ejecución PostgreSQL pendiente de instancia y driver |
| 2026-10-13 | Entorno de desarrollo sin conexión | Dependencias restauradas desde las cachés disponibles; sesión y datos de demo generados localmente | No hay credenciales de Supabase, GitHub, Cloudflare Pages o Render |
| 2026-10-13 | Revisión de navegador | La herramienta Browser no encontró navegadores conectados | Verificación visual y de extremo a extremo en navegador pendiente; continuar con componentes y API |
| 2026-10-13 | Fases 2–5: modelo relacional, permisos, API y módulos conectados | 41 tablas; 39 recursos por HTTP; 27 pruebas backend correctas; 24 pruebas frontend correctas; build de producción correcto. Pruebas de datos sobre SQLite | Ejecutar SQL y ORM en PostgreSQL; revisar diseño visual y cookies en navegador institucional |
| 2026-10-13 | Flujos integrados y reglas de negocio | Documento → tarea → carta → trámite/aprobación → evidencia validada → cierre; reunión → acuerdo → tarea idempotente → evidencia → cierre. Permisos, historial, búsquedas, duplicados, fechas, versiones y OS comprobados | No importar checks de cierre/aprobación heredados sin revisión y evidencia |
| 2026-10-13 | Migración local, demo y respaldo | Alembic 001 aplicado desde base vacía; seed repetido sin duplicar datos. Respaldo consistente con SHA-256, integrity_check, FK, versión y conteos verificados en una copia aislada | Configurar y verificar respaldo/restore PostgreSQL y almacenamiento persistente de importaciones |
| 2026-10-13 | Fuentes en Google Drive, inspección de solo lectura | ROADMAP OGC 2026 v2 y dos registros localizados; metadatos, encabezados y texto revisados; mapeo en docs/importacion-fuentes.md. No se modificaron originales ni se importaron filas reales | REGISTRO DIGITAL no devolvió celdas; exportación no materializable por restricción de red. Pendiente comprobar objetos y Excel realmente enlazados |
| 2026-10-13 | Importador CSV/XLSX y manuales | Previsualización, mapeo, validación, respaldo byte a byte, SHA-256, detección de duplicados y procedencia por fila probados con archivos ficticios. Manual, operación y configuración Render/Pages disponibles | Falta instancia/driver de PostgreSQL y accesos GitHub, Supabase, Cloudflare Pages y Render; no hay despliegue verificado |
| 2026-10-13 | Control de código y cierre local | Repositorio inicializado y archivos disponibles; inicio/detención de ambos servicios probados. Los servicios de prueba se detuvieron al concluir | El entorno permite leer .git pero rechazó crear index.lock: no fue posible agregar archivos ni crear commit. Preparar el commit desde un entorno con escritura Git |
| 2026-10-13 | Roles, tareas compartidas y revisión del jefe | XLSX local de 27 hojas leído sin modificar; autoría/asignaciones múltiples, vistas personales protegidas y avances individuales con evidencia/revisión. 34 pruebas backend, 29 frontend y build correctos; 40 recursos HTTP. Alembic 002 aplicada con respaldo y preservación de las 39 tablas históricas comprobada | Revisar visualmente el flujo en navegador; PostgreSQL continúa pendiente |
| 2026-10-13 | Registro local de participantes autorizado por el usuario | 30 nombres del XLSX registrados con procedencia, cuentas locales y perfil integrante; 30 logins comprobados; directorio/asignación disponibles. 38 pruebas backend, 30 frontend y build correctos. Flujo con dos participantes importados y cierre probado en copia aislada | Confirmar identidad del jefe y variantes de nombres; revisión visual de navegador pendiente |
| 2026-10-13 | Asignación simplificada siguiendo el Excel | Seis campos visibles; proyecto/inicio automáticos; oficinas/temáticas del XLSX registradas con procedencia. Migración 003 y preservación de registros comprobadas; 43 pruebas backend, 31 frontend, build y asignación mínima en copia aislada correctos | Revisión visual de navegador pendiente |
| 2026-10-14 | Simplificación de Tareas y responsables solicitada por el usuario | Formulario individual con tarea/responsable/plazo/instrucciones; vistas Mis tareas/Asigné/Todas según permisos; evidencia desde la ficha con nombre automático. 60 pruebas backend y 40 frontend, build y flujo real de navegador jefe → asignación → integrante → dos evidencias → validación → cierre. Revisión en 1440/768/390/320 px con datos ficticios aislados | PostgreSQL y despliegue siguen pendientes; no se modificó la base de trabajo con datos de prueba |


### Bloqueos y siguiente paso

- PostgreSQL/Supabase: instalar `requirements-postgres.txt` en un entorno con acceso a paquetes y conectar una base de prueba; ejecutar Alembic y los controles relacionales antes de cerrar las casillas correspondientes.
- REGISTRO DIGITAL: revisar dibujos/objetos y sus enlaces en una copia XLSX materializable o navegador conectado. Los Excel encontrados por búsqueda no se declaran enlazados sin comprobarlo. La lectura del libro binario exportado falló por restricción de red.
- Importación institucional: aprobar identidades, años ambiguos, equivalencia de estados y procedencia de las hojas originales. El mapeo documentado no implica que se hayan importado datos reales.
- Publicación: por elección del usuario, Render Free para interfaz/API y Supabase Free para datos/evidencias. El repositorio existente es isabel-19/Task y Render tiene sesión iniciada; faltan autenticar GitHub/Supabase, publicar el código y verificar PostgreSQL/Storage reales. Las importaciones permanecen deshabilitadas.
- Navegador: conectar Browser para comprobar escritorio/móvil, selección de relaciones, descargas y los flujos completos en la interfaz. Ver docs/verificacion.md.
