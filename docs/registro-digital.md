# Registro Digital: enlaces y numeración

## Estado y seguimiento del documento

Los emitidos muestran **Estado del documento**: Por inicio, En redacción, Listo para envío, Enviado digital, Enviado físico, Enviado físico y digital o Anulado, según las opciones del tipo en el Excel. Informes Técnicos y Cartas Múltiples conservan sus listas propias; Actas ofrece Programada, En reunión, En redacción, Compartido con las áreas participantes y Enviado. Un enlace adjunto no implica que el documento se haya enviado.

El formulario permite registrar el estado y la fecha real de envío. Desde la ficha, **Registrar envío** solicita el medio y la fecha; no aprueba una carta. Cargo, prioridad, frecuencia, atención, comentarios y enlace del correo se guardan por separado. En Recibidos se muestra formato de recepción y número del cuaderno. El dashboard cuenta recibidos pendientes de atención.

La migración `006` añade los campos de seguimiento y conserva todas las columnas anteriores. Los remitidos antiguos sin medio se muestran como **Enviado (medio sin registrar)**. La revisión completa de encabezados y listas está en [Comparación campo por campo](revision-campos-registro-2026-10-14.md).

En Registro Digital → Documentos → Nuevo registro, selecciona el tipo, la sección y el eje temático, completa el asunto, selecciona el destinatario de la lista del Excel y pega el enlace en **Documento digital**. El remitente del equipo OGC se preselecciona con tu cuenta. La sección se toma del filtro activo; sin filtro, empieza en Emitidos.

El formulario muestra el número una sola vez y toma el año de la fecha al crear. En Emitidos, el único selector de personal es **Remitente (personal OGC)**; en Recibidos, aparecen **Entidad remitente** y **Responsable de atención OGC**. Destinatario y entidad remitente usan un desplegable con búsqueda sobre los catálogos del registro. Las oficinas y entidades se extrajeron de las validaciones de datos del Excel, uniendo las listas largas concatenadas y eliminando valores repetidos. Proyecto no se solicita en Registro Digital; los documentos guardan directamente su eje temático.

Para emitidos de tipos reconocidos, **Asignar número automáticamente** está activado por defecto. El formulario muestra una sugerencia; el correlativo definitivo se asigna en la misma transacción que guarda el documento. Abrir o cancelar un formulario no consume un número. Si el guardado falla, tampoco se consume. La serie es independiente por tipo y año; las variantes «Carta» y «Carta simple» comparten serie.

## Formatos y continuidad local de 2026

Los contadores locales se inicializaron a partir de las hojas de documentos emitidos del registro de seguimiento facilitado por el usuario. Se extrajo el mayor número de cada serie entre las filas con asunto. No se importaron los documentos, personas ni enlaces del Excel.

| Tipo | Mayor correlativo del registro | Primera sugerencia tras configurar |
| --- | --- | --- |
| Carta | 500 | `CARTA N° 501-2026-UNAJMA-OGC` |
| Carta múltiple | 153 | `CARTA MÚLTIPLE N° 154-2026-UNAJMA-OGC` |
| Informe | 178 | `INFORME N° 179-2026-UNAJMA-OGC` |
| Informe técnico | 428 | `INFORME TÉCNICO N° 429-2026-UNAJMA/OGC` |
| Oficio | 010 | `OFICIO N° 011-2026-UNAJMA-OGC` |
| Acta de reunión | 111 | `ACTA DE REUNIÓN N° 112-2026-UNAJMA-OGC-SGCI` |

Los números avanzan al guardar. Las actas del libro incluyen otros sufijos, como OGC-QO; para conservar una variante concreta, desactiva la asignación automática e introduce el número completo. Los documentos recibidos y los tipos normativos conservan el número o código original de su emisor.

## Enlaces y versiones

Se admiten enlaces HTTPS de Google Drive, Google Docs y del dominio institucional `unajma.edu.pe`, incluidos sus subdominios. La casilla de acceso deja constancia de tu confirmación; la aplicación no comprueba los permisos reales del archivo.

El enlace se guarda como una versión del mismo documento, sin duplicar el registro. Editar el enlace crea una nueva versión y conserva las anteriores. Guardar de nuevo el mismo enlace y la misma confirmación no duplica una versión. Dejar el campo vacío no elimina el historial. Puedes abrir el documento desde la tabla, la tarjeta móvil o la ficha; el CSV de Documentos también incluye el enlace vigente.

## Instalación y mantenimiento

La migración `004` agrega únicamente la tabla de correlativos. Aplica las migraciones antes de iniciar una API actualizada:

```powershell
cd backend
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe ../scripts/load-document-numbering.py "<ruta privada del registro.xlsx>"
```

La última instrucción previsualiza los valores. Añade `--apply` para inicializarlos en la base configurada. El script conserva un contador que ya sea mayor y no reinicia números asignados. La configuración del año siguiente empieza en 001 salvo que existan documentos de esa serie y año o que se cargue otra referencia.

Para cargar los desplegables existentes de destinatarios:

```powershell
.venv/Scripts/python.exe ../scripts/load-document-catalogs.py "<ruta privada del registro.xlsx>" --apply
```

La migración `005` agrega el eje temático al documento y recupera el eje de los vínculos antiguos. El formulario conserva los proyectos históricos sin pedirlos ni reenviarlos al editar. También conserva destinatarios antiguos que no figuren en la lista actual; las nuevas selecciones deben pertenecer al catálogo.

## Verificación

Pruebas de API y componentes cubren sugerencias sin reserva, series por tipo y año, continuidad del registro, aliases, enlaces válidos e inválidos, versiones inmutables, exportación y rollback ante errores. Una prueba con SQLite en archivo realizó 20 asignaciones concurrentes sin duplicados. Se comprobaron también los seis correlativos a través de la API local en ejecución.

Antes de actualizar se guardaron copias SQLite en `.local/backups/`. Los controles de preservación de campos previos están en `.local/browser-audit-2026-10-14/document-registry-live.json`. La copia de revisión permanece disponible para el usuario; las acciones realizadas allí durante el trabajo pueden cambiar sus registros.

La revisión de navegador del flujo corregido comprobó tabla, ficha y formulario, las listas de Carta, Carta múltiple, Informe, Informe técnico y Acta, los formatos de Recibidos y la vista móvil de 390 px sin desbordamiento. Evidencia en `.local/browser-audit-2026-10-14/document-workflow-browser.json`. No se ha ejecutado esta migración en PostgreSQL/Supabase.
