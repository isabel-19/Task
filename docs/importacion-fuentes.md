# Mapeo observado de las fuentes

Inspección de solo lectura el 13 de octubre de 2026. No se modificaron hojas originales ni se cargaron sus registros en el entorno de prueba. Este documento conserva estructura y reglas de transformación, sin copiar filas institucionales al código o a los datos demo.

## Fuentes identificadas

- ROADMAP OGC 2026 v2: Google Sheets nativo; 27 hojas; metadatos del archivo modificados el 13 de octubre de 2026. Zona horaria del libro: `America/Los_Angeles`, que debe conciliarse con `America/Lima` al interpretar marcas de tiempo.
- 2026_Registro de seguimiento OGC.xlsx: archivo Excel, revisado mediante texto del conector; 13 bloques de hoja en la extracción. Los nombres originales de esas hojas no están preservados en el texto y quedan pendientes de lectura del XLSX.
- Lista de documentos internos: archivo Excel, texto revisado; 11 bloques. Tiene un propósito distinto del registro de seguimiento: inventario normativo, códigos, versiones, archivo y vigencia.

Las direcciones privadas de Drive se conservan fuera del repositorio; este documento publica únicamente la descripción y el mapeo estructural de las fuentes.

La lectura de estos archivos no prueba que sean los mismos enlazados por los objetos de `REGISTRO DIGITAL`. Esa asociación necesita comprobarse con el archivo exportado o desde un navegador institucional conectado.

## ROADMAP: hojas y encabezados verificados

| Hoja | sheetId | Encabezados / ubicación observada | Destino y regla |
|---|---|---|---|
| GANT | 68797689 | Fila 3: `PROYECTOS / PROCESOS`, `Actividades planificadas`, `INICIO`, `FIN`, dos columnas `STATUS`, meses ENE–DIC, `ESTADO DE AVANCE` | Proyectos/procesos y tareas. Diferenciar filas de agrupación de actividades; las dos columnas STATUS requieren selección explícita; no duplicar las tareas de las hojas mensuales |
| OCTUBRE | 572743247 | Fila 2: `Ejes tematicos`, `Participantes`, `ACTIVIDAD_TAREA (task)`, `Responsable de la actividad`, `Deadline`, `Days Left`, `STATUS`, `Done`, `STATUS/ DOCUMENTACIÓN`, `LINK DE ACCESO`, `OBSERVACIONES OGC`, `Respuesta` | Tarea + integrantes + observaciones + evidencias. `Done` o `Cerrado` no sustituyen la validación del cierre |
| TASK-JOGC | 1524818651 | Fila 4: `Responsable`, `Temática`, `Detalle`, `Tareas`, `Apoyo`, `Fecha de Inicio`, `Deadline`, `Status`, `Detalle - Actual`, `Detalles de seguimiento`, `Link de Acceso` | Tareas, asignaciones grupales, avances y evidencia; responsable/apoyo se resuelven a identidades revisadas |
| TASK-Acreditación | 1821521790 | Fila 4: `Elaborado por:`, `Modelo`, `Tareas`, `Fecha de Inicio`, `Deadline`, `Estado`, `Status`, `Comentario`, `Detalle - Actual`, `Link de Acceso` | Tareas y relación a modelos pendientes de validación; Estado y Status no se mezclan automáticamente |
| TASK-Procesos | 135481665 | Fila 4, confirmada con lectura adicional: misma familia de columnas de tareas/modelos | Tareas de proceso; preservar seriales de fecha y convertirlos en una copia tras revisar el año |
| TASK-Certificación | 467732549 | Fila 4: misma familia de columnas de tareas/modelos | Tareas; no activar normas por su presencia en esta hoja |
| TASK-Soporte Adm. | 1913513731 | Fila 4: `Elaborado por:`, `Tematica`, `Tareas`, fechas, Estado/Status, Comentario, Link | Tareas y comentarios, con origen conservado |
| TASK-Asistentes | 92061436 | Fila 3: `Resposable` (error ortográfico de origen), `Temática`, `Detalle`, `Tareas`, `Apoyo`, fechas, Status, seguimiento, Link | Alias explícito Resposable → responsable. Ignorar marcadores auxiliares, conservar el encabezado original en procedencia |
| TASK | 149798703 | Fila 3: `PROCESO`, `ITEM`, `Temática`, `Detalle`, `Acciones`, `Responsable`, `Deadline`, `Status`, `Detalle - Actual`, `Detalle - Anterior` | Tareas + historial; reconciliar con los TASK especializados |
| PAINS | 1641472569 | Fila 3: misma estructura de proceso/acciones/responsable/plazo y detalles anterior/actual | Clasificar problema, actividad o mejora; no crear una segunda tarea si ya existe en TASK |
| Entregables O/S | 266872417 | Fila 4: `Nombre`, `Modelo`, `Nro de O/S`, `N° SIAF`, `N° de Entregable`, `Fecha de Inicio de O/S`, `Deadline`, `Estado`, `Fecha de presentación`, `Fase SIAF`, `Oficina donde se encuentra`, `Link de Acceso a entregable`, `Comentario` | Agrupar por OS y separar entregables. Nombre/prestador y responsable OGC son conceptos diferentes. Fase SIAF es referencia, no una conformidad interna |
| Roles | 421625265 | Fila 1: `TEMÁTICAS`, componentes de licenciamiento, indicador, modelos SINEACE/ICACIT/ACBSP/CIEES, ISO 21001, `PROCESOS`, `TEAM OGC` | Matriz temática y de modelos, **no** roles de autenticación. Revisar vigencia antes de cargar criterios |
| Consultas_ MVs Priorizados | 1843385965 | Fila 2: `FECHA DE CONSULTA`, `PROCESO`, `MEDIOS DE VERIFICACIÓN`, `ENTREGABLES`, `ÁREAS RESPONSABLES`, `COMENTARIOS`, `CONSULTAS / REQS`, `RESPUESTAS ASESOR`, `DETALLE`, `ACUERDOS REU`, `STATUS` | Solicitudes de evidencia, dependencia externa, comentarios, compromisos; resolver a acuerdos/reuniones existentes antes de crear vínculos |
| REGISTRO DIGITAL | 1948719856 | Grilla 1000×26. Las lecturas A1:Z50 y A1:Z1000 con campos de enlaces/chips no devolvieron celdas | No declarar vacía la hoja ni inventar enlaces. Pendiente revisar objetos/dibujos y su relación con otros Excel |

Metadatos también confirman ENERO, FEBRERO, MARZO, ABRIL, MAYO, JUNIO, JULIO, AGOSTO, SETIEMBRE, DAYLIST-DICIEMBRE, TASK-Procesos y datos (oculta), INFO COMP y Datos. Se verificó el encabezado de OCTUBRE; no se afirma que todos los encabezados mensuales sean idénticos sin leerlos. Las hojas auxiliares deben clasificarse antes de ampliar la importación.

## Registro de seguimiento: encabezados observados

| Columna de origen | Destino / transformación |
|---|---|
| N° Doc | Es posible que sea un ordinal del registro. No usarlo como número documental sin contrastar `Datos del Documento` o la referencia |
| Eje Temático / Eje temático | Resolver a `axes` y al proyecto correspondiente; no duplicar un eje por mayúsculas o acentos |
| Tipo de Documento | Resolver a `document_types`, con alias revisados |
| Nombre del documento / Asunto del documento / Nombre del Documento Recibido | `documents.title` |
| Datos del Documento | Número/año/tipo documental mediante extracción revisada; no inventar valores faltantes |
| Remitente [ Pers. OGC ] | `documents.sender` y responsable OGC cuando la identidad esté confirmada; guardar cada concepto por separado |
| Destinatario(s) u Oficinas | `documents.recipient` |
| ¿Quien aprueba? / Unidad Orgánica a la que se derivó | Dependencia externa en el expediente, sin reemplazar `responsible_id` |
| Doc. de Ref. / Referencia | Resolver al documento único previo; referencias sin número inequívoco pasan al reporte de errores |
| Estatus [Elaborado], [Revisado], [Aprobado / Atendido] | Tres hechos diferentes. El último requiere acto/resolución revisada; no importar directamente un estado terminal |
| Enviado / Fecha de envio para aprobación / Fecha de envío | Preparación y fecha de remisión; mantener aprobación pendiente mientras no exista actuación validada |
| Dead Line / Deadline Fecha límite de atención | `due_date`, después de resolver año y formato |
| Days / Días restantes / Day left | No importar como datos maestros; se calculan a partir del plazo |
| Comentarios / Comentarios y/o tareas pendientes / TASK-JOGC | Historial o tarea vinculada, evitando duplicados con ROADMAP |
| Link / Link del documento / Link de Resolución de Aprobación / Link del correo | Clasificar enlace de documento, evidencia, resolución o referencia. No atribuir permisos de Drive por el texto del enlace |
| Fecha de Reunión / Asunto de la Reunión / Seguimiento a acuerdos | Reunión y acuerdos relacionados; mantener un acta documental única |

Hay columnas repetidas y filas de portada antes de los encabezados. No subir el libro directamente al importador genérico: preparar una copia por entidad con encabezado único en fila 1, eliminar columnas auxiliares vacías, resolver IDs y fechas ISO. Los bloques extraídos no reemplazan la hoja/fila original del XLSX para la procedencia definitiva.

## Inventario de documentos internos

Encabezados observados: `Nº`, `Nombre del Documento`, `Código`, `Nº Rev` o `Nº Version`, `Aprobación` o `Fecha de Aprobación`, dueño del proceso/responsable de archivar, `Oficina`, `Estado`, tipo de registro físico/electrónico, `Ubicación`, tiempo de vigencia, disposición, link de acceso y documento de referencia.

Separar el código documental del ordinal Nº; mapear nombre/código/tipo al Registro Digital normativo. La revisión o versión necesita su documento/enlace verificable. Dueño del proceso no es automáticamente el responsable OGC. Vigencia y disposición requieren política institucional de archivo; no transformarlas en plazos de tareas. El texto de modelos/ISO presente en el inventario no acredita vigencia normativa.

## Pendientes que bloquean la importación definitiva

1. Revisar los objetos de REGISTRO DIGITAL y comprobar qué archivos Excel están realmente vinculados. La exportación de referencia devolvió un archivo descargable, pero su materialización local fue rechazada por la red del entorno; no se leyó ese archivo binario.
2. Obtener nombres de hoja/fila originales de los XLSX, sin depender de los índices del texto extraído.
3. Conciliar fechas: hay fechas de otro año bajo el título ROADMAP 2026, seriales Excel, fechas sin año y textos de día/mes. No corregir el año por inferencia.
4. Resolver identidades institucionales y la equivalencia entre estados de origen y acciones autorizadas. No importar «cerrado», «pagado», «atendido» o checks de aprobación como conformidades sin evidencia.
5. Reconciliar actividades presentes en GANT, meses, TASK y PAINS; preparar y aprobar copias normalizadas con procedencia y respaldo.

Esta revisión inicial aportó el mapeo estructural. Posteriormente, por autorización expresa del usuario, se registraron únicamente los participantes del XLSX local en esta instalación: consulta [participantes](participantes.md). Las tareas, documentos, evidencias y conformidades institucionales no se importaron.
