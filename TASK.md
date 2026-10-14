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
- Los documentos pueden estar elaborados y remitidos, pero seguir pendientes de aprobación; controlar estados por separado.
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
- [ ] Publicar frontend en Cloudflare Pages y backend en Render de prueba.
- [ ] Configurar Supabase, seguridad, variables de entorno y permisos mínimos.
- [ ] Verificar funcionamiento de extremo a extremo con datos ficticios.
- [x] Documentar backups, restauración y límites de hosting gratuito.
- [x] Crear manual breve de uso y administración y checklist previo a producción institucional.

## Criterio de cierre
Una casilla solo se marca `[x]` cuando su código/documentación existe y se verificó. Nunca desplegar información institucional real en la infraestructura gratuita sin autorización y revisión de seguridad.

## Bitácora de avance
| Fecha | Tarea | Resultado / prueba | Próximo paso o bloqueo |
|---|---|---|---|
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

### Bloqueos y siguiente paso

- PostgreSQL/Supabase: instalar `requirements-postgres.txt` en un entorno con acceso a paquetes y conectar una base de prueba; ejecutar Alembic y los controles relacionales antes de cerrar las casillas correspondientes.
- REGISTRO DIGITAL: revisar dibujos/objetos y sus enlaces en una copia XLSX materializable o navegador conectado. Los Excel encontrados por búsqueda no se declaran enlazados sin comprobarlo. La lectura del libro binario exportado falló por restricción de red.
- Importación institucional: aprobar identidades, años ambiguos, equivalencia de estados y procedencia de las hojas originales. El mapeo documentado no implica que se hayan importado datos reales.
- Publicación: disponer de repositorio y accesos a Cloudflare Pages, Render y Supabase. La configuración de prueba deshabilita importaciones en Render gratuito mientras no exista respaldo persistente.
- Navegador: conectar Browser para comprobar escritorio/móvil, selección de relaciones, descargas y los flujos completos en la interfaz. Ver docs/verificacion.md.
