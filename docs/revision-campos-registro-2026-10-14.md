# Revisión campo por campo del registro documental — 14/10/2026

Fuente revisada: `C:/Users/yaque/Downloads/2026_Registro de seguimiento OGC.xlsx`.
Se extrajeron encabezados, validaciones y valores de las 13 hojas; esta comparación cubre las seis hojas documentales: Recibidos, Informes Técnicos, Cartas Simples, Informes, Cartas Múltiples y Actas.

## Corrección del flujo

Los documentos emitidos registran su preparación y envío. La columna Aprobación se sustituyó por Estado del documento en tabla, tarjetas y CSV. La ficha de emitidos oculta la aprobación histórica. Los expedientes conservan sus actuaciones; resolver un expediente ya no aprueba la carta emitida.

Estados de Cartas Simples: Por inicio, En redacción, Listo para envío, Enviado digital, Enviado físico, Enviado físico y digital, Anulado. Informes Técnicos y Cartas Múltiples usan sus listas propias. Informes añade Listo para enviar y Para revisión: se generaliza el nombre personal de la opción «Para revisión de Jack». Actas conserva Programada, En reunión, En redacción, Compartido con las áreas participantes y Enviado.

Los textos y emojis se normalizan para la interfaz, conservando el significado. En redacción representa el trabajo en proceso del documento. Adjuntar un enlace no registra un envío.

Los registros antiguos conservan sus valores; un remitido sin medio capturado aparece como Enviado (medio sin registrar). La migración añade columnas sin modificar estados ni datos anteriores. No se han importado filas documentales del Excel.

## DOCUMENTACIÓN RECIBIDA

| Celda | Campo del Excel | Uso en la aplicación |
| --- | --- | --- |
| A4 | N° Doc | Índice de fila del Excel; no se usa como correlativo del documento. El registro tiene un ID propio. |
| B4 | Eje temático | Eje temático (`axis_id`). |
| C4 | Nro de Registro Cuaderno | N.º de registro del cuaderno (`notebook_number`); no sustituye al número del documento. |
| D4 | Tipo de documento | Tipo documental (`document_type_id`). |
| E4 | Nombre del Documento Recibido | Número / nombre original (`number`). |
| F4 | Detalle de Documento | Asunto (`title`). |
| G4 | Referencia | Referencia en texto (`reference_text`); vínculos previos conservados. |
| H4 | (vacío; entidad remitente) | Encabezado vacío; la validación de H y los valores identifican a la entidad remitente (`sender`). |
| I4 | Documento recibido en formato: | Formato de recepción (`intake_format`): digital, físico o ambos. |
| J4 | Fecha de recepción | Fecha de recepción del documento recibido (`date`). En Informes Técnicos, la segunda fecha pertenece al seguimiento de la respuesta, no al envío original. |
| K4 | Unidad Orgánica a la que se derivó | Unidad de destino (`recipient`); dependencia actual e historial en el expediente asociado. |
| L4 | Estatus / [Revisado] | Actuación de revisión en el expediente (`cases` / `case-events`); no se marca automáticamente. |
| M4 | Estatus / [En elaboración] | Actuación de elaboración en el expediente; no se traslada al estado de envío de una carta emitida. |
| N4 | Estatus / [Aprobado / Atendido] | Atención del documento recibido (`approval_status`) mediante actuación autorizada; `attended` permite registrar atención. |
| O4 | ¿Quien aprueba? | Actor de la actuación autorizada en el historial del expediente; no se asigna a cartas emitidas. |
| P4 | Link del documento | Documento digital (`url`). |
| Q4 | Fecha de envió | Seguimiento de la respuesta emitida vinculada; la fecha de recepción permanece independiente. |
| R4 | Dead Line | Fecha límite (`due_date`). |
| S4 | Days | Días restantes calculados. |
| T4 | Comentarios | Comentarios (`comments`). |

Listas de estado verificadas:

- `W151 I5:I1009`: "Digital,Físico,Ambos (Fisico y Digital)".

## 8.1 Informes Técnicos

| Celda | Campo del Excel | Uso en la aplicación |
| --- | --- | --- |
| B10 | N° Doc | Índice de fila del Excel; no se usa como correlativo del documento. El registro tiene un ID propio. |
| C10 | Datos del Documento | Número del documento (`number`). |
| D10 | Asunto del documento | Asunto (`title`). |
| E10 | Remitente / [ Pers. OGC ] | Remitente OGC (`responsible_id`); emisor guardado en `sender`. |
| F10 | Destinatario(s) u Oficinas | Destinatario / oficina (`recipient`); catálogo del Excel. |
| G10 | Link | Documento digital (`url`); versiones conservadas. |
| H10 | Enviado | Estado de envío (`preparation_status`); lista específica por tipo. |
| I10 | Prioridad | Prioridad (`priority`): alta, media, baja; sin emojis. |
| J10 | Frecuencia de Seguimiento | Frecuencia (`followup_frequency`): diaria, semanal, quincenal, no es necesario. |
| K10 | Fecha de envio | Fecha real de envío (`sent_date`). |
| L10 | Deadline / Fecha limite de atención | Fecha límite de atención (`due_date`). |
| M10 | Dias restantes | Calculado desde `due_date` y la fecha actual (`days_remaining`). |
| N10 | Situación | Situación del plazo calculada (`deadline_status`); completar depende de atención, no de envío. |
| P10 | ATENDIDO | Casilla Atendido (`attended`), distinta del estado de envío. |
| Q10 | Comentarios y/o tareas pendientes | Comentarios / tareas pendientes (`comments`). |
| S10 | Fecha de recepción | Segundo bloque de seguimiento de respuesta. Se registra en un documento recibido vinculado y/o expediente con su propio plazo y atención; no se aplana sobre el envío original. |
| T10 | Deadline / Fecha limite de atención | Segundo bloque de seguimiento de respuesta. Se registra en un documento recibido vinculado y/o expediente con su propio plazo y atención; no se aplana sobre el envío original. |
| U10 | Dias restantes | Segundo bloque de seguimiento de respuesta. Se registra en un documento recibido vinculado y/o expediente con su propio plazo y atención; no se aplana sobre el envío original. |
| V10 | Situación | Segundo bloque de seguimiento de respuesta. Se registra en un documento recibido vinculado y/o expediente con su propio plazo y atención; no se aplana sobre el envío original. |
| W10 | ATENDIDO | Segundo bloque de seguimiento de respuesta. Se registra en un documento recibido vinculado y/o expediente con su propio plazo y atención; no se aplana sobre el envío original. |

Listas de estado verificadas:

- `H11:H451`: "Enviado fisico y digital,Enviado fisico,Enviado digital,En redacción,Por inicio".

## 8.2 Cartas Simples

| Celda | Campo del Excel | Uso en la aplicación |
| --- | --- | --- |
| B10 | N° Doc | Índice de fila del Excel; no se usa como correlativo del documento. El registro tiene un ID propio. |
| C10 | Datos del Documento | Número del documento (`number`). |
| D10 | Asunto del documento | Asunto (`title`). |
| E10 | Remitente / [ Pers. OGC ] | Remitente OGC (`responsible_id`); emisor guardado en `sender`. |
| F10 | Eje Temático | Eje temático (`axis_id`). |
| G10 | Destinatario(s) u Oficinas | Destinatario / oficina (`recipient`); catálogo del Excel. |
| H10 | Link | Documento digital (`url`); versiones conservadas. |
| I10 | Enviado | Estado de envío (`preparation_status`); lista específica por tipo. |
| J10 | Prioridad | Prioridad (`priority`): alta, media, baja; sin emojis. |
| K10 | Frecuencia de Seguimiento | Frecuencia (`followup_frequency`): diaria, semanal, quincenal, no es necesario. |
| L10 | Fecha de envio | Fecha real de envío (`sent_date`). |
| M10 | Deadline / Fecha limite de atención | Fecha límite de atención (`due_date`). |
| N10 | Dias restantes | Calculado desde `due_date` y la fecha actual (`days_remaining`). |
| O10 | Situación | Situación del plazo calculada (`deadline_status`); completar depende de atención, no de envío. |
| P10 | Crgo o N° de registro | Cargo o N.º de registro (`receipt_number`). |
| Q10 | ATENDIDO | Casilla Atendido (`attended`), distinta del estado de envío. |
| R10 | Comentarios | Comentarios (`comments`). |
| S10 | Link del correo | Enlace del correo (`email_url`), independiente del enlace del documento. |
| T10 | TASK-JOGC | Vínculo mediante Documentos de tareas (`task-documents`), sin duplicar tareas. |
| U10 | Responsable | Responsable de la tarea vinculada; distinto del remitente del documento. |

Listas de estado verificadas:

- `I11:I613`: "Enviado fisico y digital,Enviado fisico,Enviado digital,En redacción,Por inicio,Anulado,Listo para envio".

## 8.4 Informes enviados

| Celda | Campo del Excel | Uso en la aplicación |
| --- | --- | --- |
| B10 | N° Doc | Índice de fila del Excel; no se usa como correlativo del documento. El registro tiene un ID propio. |
| C10 | Datos del Documento | Número del documento (`number`). |
| D10 | Asunto del documento | Asunto (`title`). |
| E10 | Remitente / [ Pers. OGC ] | Remitente OGC (`responsible_id`); emisor guardado en `sender`. |
| F10 | Eje Temático | Eje temático (`axis_id`). |
| G10 | Destinatario(s) u Oficinas | Destinatario / oficina (`recipient`); catálogo del Excel. |
| H10 | Link | Documento digital (`url`); versiones conservadas. |
| I10 | Enviado | Estado de envío (`preparation_status`); lista específica por tipo. |
| J10 | Prioridad | Prioridad (`priority`): alta, media, baja; sin emojis. |
| K10 | Frecuencia de Seguimiento | Frecuencia (`followup_frequency`): diaria, semanal, quincenal, no es necesario. |
| L10 | Fecha de envio | Fecha real de envío (`sent_date`). |
| M10 | Deadline / Fecha limite de atención | Fecha límite de atención (`due_date`). |
| N10 | Dias restantes | Calculado desde `due_date` y la fecha actual (`days_remaining`). |
| O10 | Situación | Situación del plazo calculada (`deadline_status`); completar depende de atención, no de envío. |
| Q10 | ATENDIDO | Casilla Atendido (`attended`), distinta del estado de envío. |
| R10 | Comentarios | Comentarios (`comments`). |
| S10 | Link del correo | Enlace del correo (`email_url`), independiente del enlace del documento. |
| T10 | TASK-JOGC | Vínculo mediante Documentos de tareas (`task-documents`), sin duplicar tareas. |

Listas de estado verificadas:

- `I11:I246 I248:I257`: "Enviado fisico y digital,Enviado fisico,Enviado digital,En redacción,Por inicio,Listo para enviar,Para revisión de Jack".

## 8.3 Cartas Múltiples

| Celda | Campo del Excel | Uso en la aplicación |
| --- | --- | --- |
| B10 | N° Doc | Índice de fila del Excel; no se usa como correlativo del documento. El registro tiene un ID propio. |
| C10 | Datos del Documento | Número del documento (`number`). |
| D10 | Asunto del documento | Asunto (`title`). |
| E10 | Remitente / [ Pers. OGC ] | Remitente OGC (`responsible_id`); emisor guardado en `sender`. |
| F10 | Eje Temático | Eje temático (`axis_id`). |
| G10 | Destinatario(s) u Oficinas | Destinatario / oficina (`recipient`); catálogo del Excel. |
| H10 | Link | Documento digital (`url`); versiones conservadas. |
| I10 | Enviado | Estado de envío (`preparation_status`); lista específica por tipo. |
| J10 | Prioridad | Prioridad (`priority`): alta, media, baja; sin emojis. |
| K10 | Frecuencia de Seguimiento | Frecuencia (`followup_frequency`): diaria, semanal, quincenal, no es necesario. |
| L10 | Fecha de envío | Fecha real de envío (`sent_date`). |
| M10 | Deadline / Fecha límite de atención | Fecha límite de atención (`due_date`). |
| N10 | Días restantes | Calculado desde `due_date` y la fecha actual (`days_remaining`). |
| O10 | Situación | Situación del plazo calculada (`deadline_status`); completar depende de atención, no de envío. |
| Q10 | ATENDIDO | Casilla Atendido (`attended`), distinta del estado de envío. |
| R10 | Comentarios | Comentarios (`comments`). |
| S10 | Link del correo | Enlace del correo (`email_url`), independiente del enlace del documento. |
| T10 | TASK-JOGC | Vínculo mediante Documentos de tareas (`task-documents`), sin duplicar tareas. |

Listas de estado verificadas:

- `I11:I224`: "Enviado fisico y digital,Enviado fisico,Enviado digital,En redacción,Por inicio,Anulado".

## 8.5 Oficios

| Celda | Campo del Excel | Uso en la aplicación |
| --- | --- | --- |
| B10 | N° Doc | Índice de fila del Excel; no se usa como correlativo del documento. El registro tiene un ID propio. |
| C10 | Datos del Documento | Número del documento (`number`). |
| D10 | Asunto del documento | Asunto (`title`). |
| E10 | Remitente / [ Pers. OGC ] | Remitente OGC (`responsible_id`); emisor guardado en `sender`. |
| F10 | Eje Temático | Eje temático (`axis_id`). |
| G10 | Destinatario(s) u Oficinas | Destinatario / oficina (`recipient`); catálogo del Excel. |
| H10 | Link | Documento digital (`url`); versiones conservadas. |
| I10 | Enviado | Estado de envío (`preparation_status`); lista específica por tipo. |
| J10 | Prioridad | Prioridad (`priority`): alta, media, baja; sin emojis. |
| K10 | Frecuencia de Seguimiento | Frecuencia (`followup_frequency`): diaria, semanal, quincenal, no es necesario. |
| L10 | Fecha de envio | Fecha real de envío (`sent_date`). |
| M10 | Deadline / Fecha limite de atención | Fecha límite de atención (`due_date`). |
| N10 | Dias restantes | Calculado desde `due_date` y la fecha actual (`days_remaining`). |
| O10 | Situación | Situación del plazo calculada (`deadline_status`); completar depende de atención, no de envío. |
| Q10 | ATENDIDO | Casilla Atendido (`attended`), distinta del estado de envío. |
| R10 | Comentarios | Comentarios (`comments`). |
| S10 | Link del correo | Enlace del correo (`email_url`), independiente del enlace del documento. |

Listas de estado verificadas:

- `I11:I142 I144:I208 I210:I267`: "Enviado fisico y digital,Enviado fisico,Enviado digital,En redacción,Por inicio".

## 8.5 Actas - OGC

| Celda | Campo del Excel | Uso en la aplicación |
| --- | --- | --- |
| B10 | N° Doc | Índice de fila del Excel; no se usa como correlativo del documento. El registro tiene un ID propio. |
| C10 | Datos del Documento | Número del documento (`number`). |
| D10 | Asunto de la Reunión | Asunto (`title`). |
| E10 | Representante OGC en la Reunión | Representante OGC (`responsible_id`) en el formulario de actas. |
| F10 | Asistente de redacción / [ Pers. OGC ] | Asistente de redacción (`drafting_assistant_id`). |
| G10 | Unidad Orgánica que convoco a reunión | Unidad convocante (`recipient`) en el formulario de actas. |
| H10 | Link | Documento digital (`url`); versiones conservadas. |
| I10 | Estatus | Estado del acta (`preparation_status`); lista específica de actas. |
| J10 | Fecha de Reunión | Fecha de reunión (`date`) en el formulario de actas. |
| K10 | Deadline / Fecha limite para compartir Acta | Fecha límite para compartir (`due_date`). |
| L10 | Dias restantes | Calculado desde `due_date` y la fecha actual (`days_remaining`). |
| M10 | Situación | Situación del plazo calculada (`deadline_status`); completar depende de atención, no de envío. |
| O10 | Enviado y Recibido | Confirmación de atención (`attended`), separada del estado del acta. |
| P10 | Seguimiento a acuerdos | Comentarios de seguimiento (`comments`); acuerdos estructurados en Reuniones y acuerdos. |
| Q10 | Link del correo | Enlace del correo (`email_url`), independiente del enlace del documento. |

Listas de estado verificadas:

- `I11`: "Compartido con las areas participantes,En redacción".
- `I12:I35`: "Compartido con las areas participantes,En redacción,En reunión,Programada".
- `I71:I162`: "Enviado,En redacción".

## Comprobación

Pruebas de API y componentes verifican medio y fecha de envío, rechazo de fechas inconsistentes, estados por tipo, campos de seguimiento, filtros, CSV y documentos recibidos. La copia local se comprueba conservando las columnas anteriores y sus datos. PostgreSQL dispone de migración; no se ha probado contra un servidor PostgreSQL en esta sesión.
