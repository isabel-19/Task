# Manual breve de uso

## Acceso y entorno

Iniciar sesión con una cuenta asignada. El menú y los botones dependen del perfil. Los nombres con «demo» no son compromisos institucionales. Si hay participantes registrados desde el Excel, el aviso indica «Entorno local» y distingue esas personas de los registros de demostración. Las cuentas de prueba están en `.local/demo-access.txt`; los accesos de los participantes registrados están en `.local/participantes-accesos.txt`, ambos ignorados por Git. Cerrar sesión al terminar.

## Trabajo diario

El Dashboard muestra tareas pendientes, vencidas, entregas de los próximos siete días, documentos pendientes de aprobación, avance por responsable y eje y acuerdos pendientes. Los filtros cambian los contadores y listados. Haz clic en una tarjeta, tarea o proyecto para consultar su detalle. La campana abre alertas calculadas al consultar/actualizar; no envía correos ni notificaciones fuera de la aplicación.

En Proyectos crea primero ejes y procesos, luego proyectos con responsable OGC y fechas. Registra hitos y tareas relacionadas. La vista Gantt muestra hasta 100 actividades filtradas; las barras abren la ficha de tarea. Usa la tabla para paginar si hay más registros.

En Tareas, «Mi espacio» muestra tareas que te asignaron, creadas por ti o a las que agregaste integrantes. «Me asignaron», «Asigné» y «En conjunto» permiten separar esos casos. Jefatura y administración pueden consultar «Equipo» para supervisar a todos; auditoría puede consultar esa vista sin validar. La API aplica estas reglas también en enlaces directos, historial, documentos de tareas, evidencias vinculadas, búsquedas, Gantt y CSV.

Todos los integrantes pueden crear una actividad/tarea para otra persona. El formulario pide temática, actividad, responsable, apoyo y plazo; oficina y observaciones son opcionales. Los desplegables de temática/oficina usan las etiquetas del Excel. No pide un proyecto aparte, prioridad, recurrencia ni fecha de inicio. Selecciona un responsable y otros participantes, o «Asignar a todo el equipo». En la ficha, «Agregar participantes» permite invitar a más integrantes conservando los aportes anteriores. Los usuarios deben estar activos y tener permiso de trabajo en tareas. Quien creó la tarea o el jefe puede editar su descripción y fechas; los participantes registran aportes sin cambiar los de sus compañeros. El responsable se conserva cuando ya existen avances.

«Registrar mi avance» guarda tu porcentaje individual, comentario y evidencia en una misma operación. Adjunta un enlace HTTPS de Google Drive/Docs y confirma que el jefe puede acceder. La aplicación guarda enlaces; no sube archivos ni consulta automáticamente los permisos de Drive. Los comentarios y observaciones no requieren evidencia. Un avance queda pendiente hasta que el jefe lo revise.

En «Avances del equipo» se muestran los porcentajes reportados y validados por persona. El porcentaje consolidado es el promedio del último aporte validado de cada participante; quien aún no tiene aporte validado cuenta como cero. Un envío nuevo pendiente conserva el porcentaje validado anterior. El jefe abre la evidencia, pulsa «Revisar avance» y valida o deja observaciones. La persona observada registra otro avance con la corrección; el historial conserva ambos envíos y la revisión. Los avances anteriores al último envío no se pueden validar.

El cierre exige que el último aporte de cada participante esté validado al 100 %, además de las dependencias y subtareas cerradas. Solo jefatura/administración puede cerrar con la última versión validada de una evidencia vinculada o con una justificación autorizada. El cierre actualiza el acuerdo de origen; una tarea recurrente conserva su autor y equipo en la siguiente ocurrencia. Dashboard y Reportes ofrecen también «Mi espacio»/«Equipo» para los perfiles autorizados.

Los porcentajes de demostración o históricos que existían antes de esta actualización se conservan; no se convierten en validaciones del jefe. Las filas sin autor de creación recuperable se mantienen sin inventar una identidad. Para cerrar una tarea anterior, sus participantes deben registrar y obtener validación de sus aportes.

Registro Digital tiene Emitidos, Recibidos, Normativos/técnicos y Archivo digital. Guarda una vez cada documento por número/año/tipo/emisor. Los vínculos usan el mismo registro; no lo dupliques para relacionarlo con otra tarea. Registra las versiones mediante enlaces institucionales y confirma permisos. «Registrar envío» conserva la aprobación pendiente. Usa un expediente para registrar revisión, firma, derivación, observaciones, subsanación y aprobación/atención con documento de resolución.

En Reuniones registra fecha/hora, agenda, lugar, asistentes y documento de acta. Añade acuerdos con responsable, proyecto y plazo. «Crear tarea» conserva esos datos y produce una sola tarea. Su cierre actualiza el cumplimiento del acuerdo; consulta los acuerdos en la próxima reunión.

En Evidencias registra nombre, categoría, fecha, solicitud a un área y plazo. Agrega una versión con enlace HTTPS autorizado de Drive/Docs, confirma que las personas pertinentes tienen acceso y solicita validación. El sistema registra la confirmación humana de permisos; no consulta los permisos de Google Drive automáticamente. Cada vínculo tiene exactamente un destino. Una nueva versión necesita otra validación.

Entregables OS conserva número OS, SIAF opcional, prestador, responsable y plazo. En cada entregable vincula el documento de presentación. Un revisor autorizado registra en revisión, observado o conforme. Este seguimiento no reemplaza SIGA/SIAF.

Indicadores permite registrar modelos, criterios, periodos, metas, resultados y mejoras relacionadas con tareas. No hay estándares institucionales precargados como vigentes. Revisar fuente y versión antes de activar un modelo; cambiar versión/fuente devuelve el modelo y sus criterios a pendiente de validación. Los resultados son únicos por indicador/periodo. Los porcentajes admiten 0–100.

Reportes exporta CSV UTF-8 con filtros de responsable, eje, periodo y plazo; los botones de 7/30 días filtran por fechas. No confundirlos con resúmenes de cambios realizados en ese periodo: las tareas se filtran por plazo. Puede exportarse un listado de tareas/acuerdos vencidos. La exportación evita fórmulas ejecutables desde contenido de texto.

## Administración

En Tareas, «Participantes del equipo» permite buscar los nombres registrados y crear una tarea para una persona. La lista señala posibles variantes de escritura y su procedencia. La [guía de participantes](participantes.md) explica los identificadores locales, el registro y la conservación de identidades existentes.

Crear usuarios con contraseñas de al menos 12 caracteres, asignar roles y configurar permisos por acción. La ficha permite retirar asignaciones y desactivar otras cuentas; cambiar contraseña o desactivar una cuenta revoca sus sesiones. No puede desactivarse la propia cuenta ni retirar su rol de recuperación administrador. El catálogo de permisos es fijo; pueden crearse roles que combinen permisos existentes.

La bitácora muestra quién creó o cambió cada registro, con valores anteriores y posteriores. Consulta/auditoría puede consultarla, sin modificar registros. Las ediciones detectan revisiones desactualizadas; al recibir un conflicto, actualiza y revisa antes de reintentar.

Importar solo después de leer [el procedimiento de importación](importacion.md) y [el mapeo de fuentes observado](importacion-fuentes.md). Revisar la previsualización antes de confirmar. Los encabezados principales ya fueron revisados; los objetos de REGISTRO DIGITAL, Excel vinculados, identidades y fechas ambiguas siguen pendientes.

La [guía de asignación simple](asignacion-simple.md) explica los campos y su relación con el Excel, la conservación de actividades anteriores y la migración 003.
