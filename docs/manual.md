# Manual breve de uso

## Acceso y entorno

Iniciar sesión con una cuenta asignada. El menú y los botones dependen del perfil. Los nombres con «demo» no son compromisos institucionales. Si hay participantes registrados desde el Excel, el aviso indica «Entorno local» y distingue esas personas de los registros de demostración. Las cuentas de prueba están en `.local/demo-access.txt`; los accesos de los participantes registrados están en `.local/participantes-accesos.txt`, ambos ignorados por Git. Cerrar sesión al terminar.

## Trabajo diario

El Dashboard muestra tareas pendientes, vencidas, entregas de los próximos siete días, documentos recibidos pendientes de atención, avance por responsable y eje y acuerdos pendientes. Los filtros cambian los contadores y listados. Haz clic en una tarjeta, tarea o proyecto para consultar su detalle. La campana muestra plazos y evidencias pendientes de revisión para jefatura. Los avisos se actualizan automáticamente cada 30 segundos y al volver a la ventana. Un aviso de evidencia permanece hasta validar el envío o dejar observaciones. Consulta [avisos de evidencias](notificaciones-evidencias.md).

En Proyectos crea primero ejes y procesos, luego proyectos con responsable OGC y fechas. Registra hitos y tareas relacionadas. La vista Gantt muestra hasta 100 actividades filtradas; las barras abren la ficha de tarea. Usa la tabla para paginar si hay más registros.

En Tareas y responsables, «Mis tareas» muestra las tareas que tienes asignadas y «Tareas que asigné» las que creaste para otras personas. Jefatura, administración y auditoría pueden consultar «Todas las tareas» según sus permisos. El listado muestra tarea, responsable, fecha límite, avance reportado y estado. La API protege también el detalle, el historial y las evidencias.

«Asignada por» muestra quién creó la asignación debajo del título en el listado y las tarjetas móviles, en la agenda y en la cabecera de la ficha. Se mantiene visible en las pestañas de entrega y evidencias. El dato no se reemplaza por quien editó o revisó después; si una tarea histórica no tiene autor recuperable, indica «No registrado».

Pulsa «Asignar tarea» y completa qué deben hacer, selecciona una o varias personas en «Asignar a» y establece la fecha límite. Las instrucciones son opcionales. «Añadir personas» permite incorporar más integrantes desde la ficha. Puedes buscar al responsable por nombre. La tarea aparece en «Mis tareas» de cada persona seleccionada; quien la asignó la encuentra en «Tareas que asigné». La clasificación y fecha de inicio se resuelven internamente. Al editar se conservan las relaciones y configuración anteriores.

Cada integrante pulsa «Añadir evidencia» en su listado y encuentra el formulario «Añadir mi evidencia» directamente en la ficha. Escribe qué realizó y su porcentaje; elige «Archivo de mi equipo» para adjuntar un archivo del escritorio o «Enlace Drive/Docs» para usar un enlace HTTPS. Solo el enlace requiere confirmar que jefatura puede abrirlo. El nombre de la evidencia se genera automáticamente y cada envío queda en el historial, incluso varios el mismo día. La aplicación no comprueba permisos de Drive automáticamente.

La carga admite un archivo por envío, hasta 20 MB por defecto: PDF, PNG, JPG/JPEG, WEBP, DOCX, XLSX, TXT o CSV. Después de enviarlo, «Previsualizar» abre el visor desde la tabla, agenda o historial, y «Descargar» conserva el original con su nombre. Los archivos quedan sujetos a los permisos de la tarea. El envío genera el mismo pendiente de revisión para jefatura que un enlace.

El visor muestra PDF e imágenes directamente; Word muestra el texto y Excel/CSV las celdas disponibles. Esta vista de contenido no reproduce todos los formatos, imágenes internas, gráficos ni cálculos de Office. Para verlos completos, descarga el original. Las vistas extensas se limitan a 100.000 caracteres o tres hojas con 100 filas y 20 columnas; el archivo original permanece completo. No se envían documentos a servicios externos para generar la vista previa.

«Cuentas vinculadas», en la cabecera, permite conectar Google o Microsoft cuando administración haya habilitado esas aplicaciones. En Añadir evidencia, «Google / Microsoft» permite elegir el documento desde Google Drive o OneDrive. El envío conserva una copia privada, su origen y el pendiente de revisión; jefatura no necesita entrar en la cuenta del integrante para revisar esa copia. Los adjuntos de Outlook deben estar en OneDrive o subirse desde el equipo. Consulta [vinculación y activación](cuentas-google-microsoft.md).

La ficha muestra responsable, fecha límite, quién asignó, instrucciones y avances/evidencias. El avance reportado se distingue del validado. Jefatura abre la evidencia y pulsa «Revisar avance» para validar o dejar observaciones. El responsable puede enviar otra evidencia con la corrección; las anteriores se conservan. En una tarea compartida, cada integrante conserva su porcentaje y evidencia, firmados con su propia cuenta. No necesita editar la asignación para aportar evidencias.

La ficha separa «Resumen», «Evidencias» y «Añadir evidencia». Al pulsar «Enviar evidencia a revisión» pasa al historial y muestra que está pendiente de jefatura. La descripción de quien entrega y la respuesta de jefatura se muestran por separado. Otra persona de jefatura debe revisar el envío, también cuando quien entrega tiene permisos de administrador.

«Abrir documento» permite entrar al enlace directamente desde la tabla o la agenda; «Ver evidencias» abre el historial completo. Los documentos vinculados de Registro Digital y las evidencias anteriores también permanecen accesibles. La vista «Agenda semanal» organiza los mismos resultados por fecha límite y permite navegar entre semanas o volver a «Hoy». Pendiente/vencida se distingue en rojo, en progreso en amarillo, en revisión en azul y cerrada/validada en verde. Consulta [agenda y evidencias](agenda-evidencias-azul.md).

Cuando el último avance de todos los participantes está validado al 100 %, jefatura puede pulsar «Cerrar tarea» y confirmar. Se utiliza una evidencia validada del historial y el servidor comprueba nuevamente los requisitos, incluidas dependencias y subtareas anteriores. El cierre actualiza el acuerdo de origen. Dashboard y Reportes conservan sus vistas y permisos propios.

Los porcentajes de demostración o históricos que existían antes de esta actualización se conservan; no se convierten en validaciones del jefe. Las filas sin autor de creación recuperable se mantienen sin inventar una identidad. Para cerrar una tarea anterior, sus participantes deben registrar y obtener validación de sus aportes.

Registro Digital tiene Emitidos, Recibidos, Normativos/técnicos y Archivo digital. Guarda una vez cada documento por número/año/tipo/emisor. Los vínculos usan el mismo registro; no lo dupliques para relacionarlo con otra tarea. Registra las versiones mediante enlaces institucionales y confirma permisos. En emitidos selecciona el estado de preparación o envío y su fecha real; «Registrar envío» distingue digital, físico o ambos. Una carta emitida no se aprueba. La atención de recibidos se registra por separado, con sus formatos, referencias, plazos y actuaciones del expediente. Consulta la [revisión campo por campo](revision-campos-registro-2026-10-14.md).

En Reuniones registra fecha/hora, agenda, lugar, asistentes y documento de acta. Añade acuerdos con responsable, proyecto y plazo. «Crear tarea» conserva esos datos y produce una sola tarea. Su cierre actualiza el cumplimiento del acuerdo; consulta los acuerdos en la próxima reunión.

En Evidencias registra nombre, categoría, fecha, solicitud a un área y plazo. Agrega una versión con enlace HTTPS autorizado de Drive/Docs, confirma que las personas pertinentes tienen acceso y solicita validación. El sistema registra la confirmación humana de permisos; no consulta los permisos de Google Drive automáticamente. Cada vínculo tiene exactamente un destino. Una nueva versión necesita otra validación.

Entregables OS conserva número OS, SIAF opcional, prestador, responsable y plazo. En cada entregable vincula el documento de presentación. Un revisor autorizado registra en revisión, observado o conforme. Este seguimiento no reemplaza SIGA/SIAF.

Indicadores permite registrar modelos, criterios, periodos, metas, resultados y mejoras relacionadas con tareas. No hay estándares institucionales precargados como vigentes. Revisar fuente y versión antes de activar un modelo; cambiar versión/fuente devuelve el modelo y sus criterios a pendiente de validación. Los resultados son únicos por indicador/periodo. Los porcentajes admiten 0–100.

Reportes exporta CSV UTF-8 con filtros de responsable, eje, periodo y plazo; los botones de 7/30 días filtran por fechas. No confundirlos con resúmenes de cambios realizados en ese periodo: las tareas se filtran por plazo. Puede exportarse un listado de tareas/acuerdos vencidos. La exportación evita fórmulas ejecutables desde contenido de texto.

## Administración

En **Cuentas vinculadas → Habilitar conexiones para todos los usuarios**, jefatura configura una sola vez el registro Google/Microsoft de la oficina. Los integrantes con permiso para trabajar en tareas conectan después sus propias cuentas, sin configurar aplicaciones ni conocer secretos. Cada persona ve solo sus conexiones. La configuración central se aplica al guardar; las credenciales guardadas se conservan dejando sus campos vacíos. Consulta la [guía de activación](cuentas-google-microsoft.md).

Cada persona puede usar su propio Google para consultar archivos propios o compartidos con ella. **Explorar y previsualizar** abre Drive desde Cuentas vinculadas sin exigir una tarea ni enviar una evidencia; el selector distingue Todos los archivos, Compartidos conmigo y unidades compartidas. Al presentar una evidencia de Google también puede previsualizarse antes de enviar. Los permisos y las restricciones de copia del propietario se respetan. Mientras Google mantenga el registro en modo Prueba, administración debe añadir los otros correos a los usuarios de prueba del proveedor.

Jefatura tiene el mismo nivel de acceso que Administrador y puede gestionar usuarios, roles, catálogos e importaciones. Ambos perfiles mantienen la supervisión y revisión de tareas. La cuenta conserva su denominación «jefatura». Consulta [jefatura y administración](jefatura-administracion.md).

El selector «Responsable» de Tareas permite buscar a las personas registradas y asignarles una tarea. La [guía de participantes](participantes.md) explica los identificadores locales, el registro y la conservación de identidades existentes.

Crear usuarios con contraseñas de al menos 12 caracteres, asignar roles y configurar permisos por acción. La ficha permite retirar asignaciones y desactivar otras cuentas; cambiar contraseña o desactivar una cuenta revoca sus sesiones. No puede desactivarse la propia cuenta ni retirar su rol de recuperación administrador. El catálogo de permisos es fijo; pueden crearse roles que combinen permisos existentes.

La bitácora muestra quién creó o cambió cada registro, con valores anteriores y posteriores. Consulta/auditoría puede consultarla, sin modificar registros. Las ediciones detectan revisiones desactualizadas; al recibir un conflicto, actualiza y revisa antes de reintentar.

Importar solo después de leer [el procedimiento de importación](importacion.md) y [el mapeo de fuentes observado](importacion-fuentes.md). Revisar la previsualización antes de confirmar. Los encabezados principales ya fueron revisados; los objetos de REGISTRO DIGITAL, Excel vinculados, identidades y fechas ambiguas siguen pendientes.

La [guía de asignación simple](asignacion-simple.md) explica el flujo actual y la conservación de las actividades anteriores.
