# Navegación y permisos

| Ruta | Módulo | Registros relacionados |
|---|---|---|
| `/` | Dashboard | pendientes, alertas, proyectos, tareas, documentos |
| `/proyectos` | Proyectos y Roadmap | ejes, procesos, proyectos, hitos, dependencias |
| `/tareas` | Tareas y responsables | tareas, asignaciones, subtareas, avances, cierre |
| `/registro` | Registro Digital | documentos, tipos, versiones, referencias, vínculos |
| `/tramites` | Seguimiento de trámites | expedientes, actuaciones, resoluciones |
| `/reuniones` | Reuniones y acuerdos | reuniones, asistentes, actas, acuerdos, tareas |
| `/evidencias` | Evidencias | versiones, solicitudes, relaciones, validaciones |
| `/servicios` | Entregables OS | órdenes, entregables, presentación, conformidad |
| `/indicadores` | Indicadores y calidad | modelos, criterios, periodos, resultados, mejoras |
| `/reportes` | Reportes y alertas | filtros, exportación CSV, vencimientos |
| `/administracion` | Administración | usuarios, roles, permisos, catálogos, auditoría |

El navegador usa rutas protegidas y permisos para los botones; la API comprueba sesión y permisos en cada petición. La ruta de acceso es `/login`. Sin credenciales, todos los recursos de negocio responden 401.

| Perfil | Consultar | Crear/editar | Validar/cerrar | Administrar |
|---|---|---|---|---|
| Administrador | Todos | Todos | Sí | Sí |
| Jefatura | Todos | Todos | Sí | Sí, mismo nivel que administrador |
| Coordinador | Operativos; tareas de su espacio | Operativos y asignaciones de tareas | Otros módulos; avances/cierre de tareas reservados al jefe | No |
| Integrante | Operativos; tareas de su espacio | Operativos propios; crear tareas para colegas y registrar su aporte en tareas compartidas | No | No |
| Consulta/auditoría | Todos los registros operativos y bitácora | No | No | No |

Los permisos se guardan como `módulo.read`, `módulo.write`, `módulo.validate`, con asignaciones por rol. La administración permite añadir y retirar permisos. Auditoría y transiciones son solo lectura por CRUD general; se escriben en acciones controladas. Un integrante no puede reasignarse una tarea ajena ni cambiar al responsable para apropiarse de un registro. Desactivar un usuario revoca sus sesiones.

Jefatura tiene el mismo nivel administrativo que Administrador: usuarios, roles, catálogos, importaciones y auditoría, además de supervisión, revisión y cierre de tareas. Conserva su nombre de rol «jefatura». La migración 007 añade los permisos faltantes en instalaciones existentes; las instalaciones nuevas crean ambos roles con los mismos permisos. Cada rol conserva las protecciones para no retirar sus propios accesos administrativos. Consulta [jefatura y administración](jefatura-administracion.md).

La supervisión de tareas usa `tasks.supervise` (jefatura/administrador). La vista de auditoría usa `tasks.team_read`, que no permite revisar ni cerrar. `tasks.validate` por sí solo no permite validar tareas sin supervisión. En Tareas la vista predeterminada es «Mis tareas» (asignadas a la persona); «Tareas que asigné» consulta las creadas por ella. Los perfiles autorizados pueden elegir «Todas las tareas» para consultar el conjunto. Avances y evidencias se consultan dentro de la ficha, sin pestañas de recursos internos.
