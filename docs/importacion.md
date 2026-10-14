# Importación y revisión de fuentes

Se localizaron en Google Drive `ROADMAP OGC 2026 v2`, `2026_Registro de seguimiento OGC.xlsx` y la lista de documentos internos. Se revisaron metadatos, encabezados y texto de referencia en modo de solo lectura. El mapeo observado está en [importacion-fuentes.md](importacion-fuentes.md); no se importaron registros institucionales a la aplicación. Los enlaces contenidos en objetos de `REGISTRO DIGITAL` siguen pendientes: las lecturas de celda no devolvieron contenido y el entorno impidió materializar la copia exportada para revisar sus dibujos/relaciones. No se asumen revisados esos Excel.

| Hoja o fuente esperada | Destino | Mapeo inicial propuesto | Revisión necesaria |
|---|---|---|---|
| Gantt / meses | projects, tasks, milestones, task_dependencies | eje/proceso → catálogos; actividad → título; fechas → ISO; responsable → UUID | Unificar actividades repetidas en hojas mensuales; verificar fechas y dependencias |
| TASK | tasks, task_assignments, task_updates | título, prioridad, plazo, progreso, comentarios | Conciliar con Gantt; estados de cierre no se importan por CRUD |
| PAINS | improvement_plans / observaciones | problema → título/descripción; relación a indicador/tarea | Distinguir problema de actividad y evitar duplicados |
| Roles | axes, processes, quality_models, criteria y asignaciones revisadas | matriz de temáticas, componentes, modelos, procesos y TEAM OGC | No es un catálogo de perfiles de acceso. Validar vigencia de criterios; crear usuarios y permisos por administración |
| Entregables OS | service_orders, deliverables | OS, SIAF, prestador, plazo, presentación | Conformidad requiere una actuación autorizada, no una casilla de Excel |
| Consultas / medios de verificación | evidence, evidence_versions, evidence_links | medio, categoría, área, autor, enlace | Confirmar permisos institucionales de Drive y versión antes de validar |
| REGISTRO DIGITAL | documents, document_versions, cases | número, año, tipo, asunto, emisor/destinatario, referencia, envío, plazo | Elaborado/revisado/aprobado se mapean a flujos distintos; revisar enlaces a Excel |
| Registro documental interno | documents, cases, case_events | N.º, eje, tipo, nombre, aprobador externo, referencia, fecha de envío, resolución | No confundir aprobación con remisión; conservar origen y respaldo |

El importador disponible en Administración acepta CSV UTF-8 y XLSX, con un máximo de 5 MB, 20 MB descomprimidos, 1 000 filas por hoja y 200 columnas. Normaliza encabezados Unicode, propone coincidencias exactas y permite seleccionar columnas o constantes. Las claves relacionadas se eligen de registros previos; no se inventan identidades. Las fechas de importación deben ser texto ISO `AAAA-MM-DD` (y fecha/hora ISO para reuniones). Los seriales de fecha Excel y fórmulas necesitan revisión y conversión en una **copia** antes de importar; no se evalúan fórmulas.

Orden: ejes/procesos/usuarios/catálogos → proyectos → tareas/documentos/reuniones/OS → acuerdos/entregables/indicadores → vínculos y validaciones. Las entidades autorizadas por el importador son proyectos, tareas, documentos, reuniones, acuerdos, OS, entregables, indicadores y resultados. Versiones, vínculos e historiales se registran por las acciones de sus módulos para preservar controles.

1. Trabajar con copias de las fuentes. Conservar el archivo original y registrar su SHA-256.
2. Leer encabezados, hojas y muestra. Los enlaces externos XLSX se **enumeran**, sin visitarlos, descargarlos ni asumir que fueron importados.
3. Elegir una hoja y mapear campos; asociar responsables y catálogos mediante UUID. Convertir formatos en una copia de trabajo.
4. Previsualizar. El servidor valida campos, fechas, referencias y duplicados contra la fuente y la base. Los errores muestran la fila de origen.
5. El respaldo conserva exactamente los bytes recibidos en `backend/storage/imports`; solo el backend tiene acceso a esa carpeta.
6. Revisar y confirmar. Una importación con errores se rechaza. Al confirmar se revalidan todas las filas dentro de una transacción; si falla una, ninguna se guarda.
7. `import_sources` conserva lote/archivo/hoja/fila/entidad/ID; la auditoría registra la operación. Un lote no puede confirmarse dos veces. Un mismo archivo/hoja/destino no admite lotes duplicados.

Para corregir una previsualización, generar una nueva copia de trabajo corregida (un nuevo hash), conservando el respaldo anterior. Falta resolver identidades y fechas ambiguas, revisar los libros enlazados, confirmar las hojas de los XLSX en sus archivos originales y aprobar el mapeo definitivo. No debe marcarse la casilla de revisión de Excel enlazados hasta hacerlo.
