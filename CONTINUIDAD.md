# Informe de continuidad — ROADMAP OGC · UNAJMA

Última actualización: **16 de octubre de 2026, hora de Perú**.
Último trabajo completado: respaldo cifrado y restauración local verificados; migración 011 aplicada en Supabase, commit funcional `741fdfb` subido a GitHub y desplegado en Render. Avisos de reuniones probados con dos cuentas en navegadores aislados y por HTTP. BOOTSTRAP_* retirados y acceso de jefatura comprobado después del despliegue. El SQL de hardening quedó excluido del commit y conserva su cambio local. Informe: [publicacion-reuniones-2026-10-16.md](docs/publicacion-reuniones-2026-10-16.md).

## Dónde nos quedamos

**La aplicación ya está publicada y el propietario confirmó que pudo ingresar.** La última revisión de la web y de PostgreSQL pasó correctamente. No hay un fallo funcional detectado pendiente de corregir en el alcance de esa revisión.

| Recurso | Estado / ubicación |
| --- | --- |
| Aplicación pública | https://roadmap-ogc.onrender.com |
| Repositorio existente | https://github.com/isabel-19/Task |
| Servicio Render | `roadmap-ogc`, Free, Docker; interfaz y API juntas |
| Panel Render | https://dashboard.render.com/web/srv-db8idot9fdbs73edpthg/env |
| Supabase | PostgreSQL y bucket privado `roadmap-evidence`, plan gratuito |
| Panel Supabase | https://supabase.com/dashboard/project/wpuukkfszfilkvsmoyct |
| Base | Esquema `roadmap`, migración `011` aplicada el 16 de octubre; ejecución con rol restringido `roadmap_api` |
| Configuración seleccionada | `render.yaml` de la raíz. `deploy/render.production.yaml` es una alternativa de pago que no se aplicó |

**Siguiente paso concreto:** conservar una copia privada externa del respaldo y sus claves; después continuar con la vinculación personal de Google si el propietario lo solicita. La publicación de reuniones, la migración 011, la retirada de BOOTSTRAP_* y las pruebas con dos cuentas están terminadas. Frontend y API siguen juntos; no se creó un sitio estático separado.

El propietario puede cerrar sesión. Para retomar, abrir esta misma carpeta y leer este archivo; `AGENTS.md` lo establece como primer paso. La disponibilidad futura del navegador conectado debe comprobarse de nuevo.

## Almacenamiento consultado

Consulta directa de solo lectura realizada el **15 de octubre de 2026 a las 17:01, hora de Perú**. Las cuotas Free se contrastaron ese día con la [tarifa oficial de Supabase](https://supabase.com/pricing).

| Espacio | Cuota gratuita publicada | Uso consultado |
| --- | --- | --- |
| Base PostgreSQL del proyecto | 500 MB | 15.152.819 bytes: aproximadamente 15,15 MB decimales, o 14,45 MiB; cerca del 3 % de 500 MB |
| Archivos de ROADMAP en el bucket privado | 1 GB de Storage incluido en el plan | 3 objetos, 180 bytes en total, según sus metadatos de Storage |

La cifra anterior de 14,45 «MB» del informe de validación utilizaba unidades binarias; corresponde a los mismos aproximadamente 15,15 MB decimales. El esquema `roadmap`, con tablas e índices, ocupa aproximadamente 3 MiB dentro del total de PostgreSQL consultado. La cuota incluye más espacio que solo las filas de tareas.

Los registros de usuarios, tareas, fechas y comentarios consumen la cuota de base de datos; los PDF, imágenes y demás adjuntos usan Storage, un espacio separado. La configuración del bucket conserva el límite de **20 MiB por archivo** (20 MB en la interfaz). Las evidencias copiadas desde proveedores externos también usan Storage.

La medición se hizo con `pg_database_size(current_database())` y los metadatos de `storage.objects`; es una lectura puntual de la base principal y del bucket de ROADMAP, no el total de métricas de facturación de la organización. Los límites y el uso facturado deben consultarse en el panel si se añaden proyectos o buckets. Véase la [explicación oficial de tamaño de base](https://supabase.com/docs/guides/platform/database-size).

Resultado sin secretos guardado en `.local/qa/render-2026-10-15/storage-usage.json`; script privado `.local/render-storage-usage.py`. No se necesitó cambiar el plan ni ampliar almacenamiento. El siguiente paso de configuración sigue siendo retirar `BOOTSTRAP_*`.

## Qué se ha construido y configurado

- Aplicación Vue 3 + Quasar y API FastAPI con sesiones, roles y permisos aplicados en el servidor.
- Once módulos: dashboard, proyectos/roadmap, tareas, Registro Digital, trámites, reuniones/acuerdos, evidencias, entregables OS, indicadores/calidad, reportes/alertas y administración.
- Tareas con una o varias personas asignadas, vistas personales y de equipo, agenda, avances por integrante, avisos a jefatura, revisión y cierre.
- Documentos con enlaces, numeración por tipo/año y seguimiento de envío/respuesta.
- Evidencias desde el equipo con carga privada, previsualización y descarga. Soporte de PDF, imágenes, Word, Excel, TXT y CSV.
- Configuración central cifrada de Google/Microsoft y vinculación personal por usuario. Google Drive/Picker se preparó y comprobó en el entorno local; la vinculación personal en la web publicada sigue pendiente.
- Participantes y catálogos del Excel registrados en el entorno local en sesiones anteriores. **No asumir que esos usuarios o datos se transfirieron a la web**. La publicación comenzó con jefatura y las pruebas remotas utilizaron datos ficticios.
- Contenedor Docker, dependencias corregidas para Linux, origen HTTPS de Render y migraciones al arranque. PostgreSQL y archivos persistentes residen en Supabase.
- Manuales, instrucciones de importación, operación y despliegue. Las importaciones están deshabilitadas en la publicación.

El detalle histórico de cada fase y sus pruebas está en [TASK.md](TASK.md); el uso del sistema está en [el manual](docs/manual.md).

## Última validación completada

Informe detallado: [verificacion-render-2026-10-15.md](docs/verificacion-render-2026-10-15.md).

| Área | Evidencia registrada |
| --- | --- |
| Salud de producción | HTTPS; PostgreSQL; `production`; `demo=false` |
| Base real | 47 tablas del modelo y sus columnas; migración 010; 128 relaciones sin huérfanos; 146 restricciones FK/CHECK validadas |
| Seguridad de la base | TLS en ambas conexiones; rol limitado; esquema inaccesible para `anon`/`authenticated`; historial protegido |
| Estado de índices/conexiones | Cero índices inválidos y cero conexiones bloqueadas en el momento de la consulta |
| API publicada | 40 recursos más 10 consultas auxiliares/reportes respondieron correctamente |
| Navegador | 11 módulos y Cuentas vinculadas sin errores observados; listado de tareas y evidencia abiertos; escritorio y móvil revisados |
| Flujo real | Jefatura asigna → integrante carga y previsualiza archivo → aviso → revisión → cierre |
| Privacidad y sesión | Rechazo sin sesión, de autorrevisión del integrante, de operaciones sin CSRF y de origen ajeno |
| Storage real | Bucket privado; subida/lectura íntegra; acceso público rechazado; objeto técnico temporal eliminado |
| Persistencia | Tarea y archivo recuperados en una nueva sesión, con SHA-256 correcto. No se reinició Render en esa revisión |
| Suites locales | 104 pruebas de backend y 75 de interfaz correctas |

La cuenta creada para la última prueba quedó desactivada y su tarea cerrada. En la inspección de Todas las tareas había **tres tareas ficticias cerradas** de las comprobaciones del despliegue; se conservaron sus archivos e historial. No confundirlas con trabajo institucional.

## Pendientes, en orden sugerido

1. Conservar fuera del equipo una copia privada del respaldo y el material necesario para descifrarlo. Publicación de 011, avisos y acceso posterior al retiro de BOOTSTRAP_* comprobados; no repetirlos como trabajo pendiente.
2. Vincular la cuenta personal de Google desde Cuentas vinculadas en la web y probar selección, previsualización y entrega de un archivo autorizado. La configuración central está presente, pero jefatura aparecía **sin vincular**. No afirmar que Drive ya fue validado en producción.
3. Habilitar Microsoft si el propietario lo necesita: la aplicación externa y sus credenciales todavía no están configuradas.
4. Conservar una copia privada externa del respaldo y sus claves. El 16 de octubre se verificó la restauración local aislada del esquema roadmap completo, los conteos y la integridad de evidencias/claves del respaldo previo a 011.
5. Registrar los integrantes autorizados en la publicación. Revisar identidades y procedencia antes de importar información institucional.
6. Revisar los Excel realmente enlazados en Registro Digital; el mapeo previo no confirma por sí solo todos los enlaces del libro original.
7. Conservar el cambio local de `database/supabase-hardening.sql`, excluido del envío por indicación del propietario. El código de reuniones y la documentación previa ya se incorporaron a GitHub; comprobar git status al retomar. La separación de un frontend estático quedó como opción sin confirmar.

No se probaron escrituras reales de todos los módulos. Sí se comprobaron la publicación de reuniones con dos cuentas y la recuperación de una tarea y evidencia anteriores después del nuevo despliegue. El estado aquí descrito es el de la última comprobación, no una garantía permanente del proveedor gratuito.

## Estado local y de Git

Último commit funcional publicado: `741fdfb` — Publicar avisos privados de reuniones con migración 011 y continuidad. Render lo desplegó con ID `dep-db94fb6k1f9s73eqrfjg`. Las notas de cierre se guardan por separado con `[skip render]`; consultar `git status` y `git log` al retomar para su commit concreto.

Cambios locales presentes antes de preparar este informe:

- `README.md`, `TASK.md`, `docs/publicacion-web.md` y `docs/render-gratuito.md`: actualización del estado real y de las pruebas.
- `docs/verificacion-render-2026-10-15.md`: informe de validación nuevo, aún sin commit.
- `database/supabase-hardening.sql`: cambio previo que concede UPDATE únicamente sobre `evidence_versions.revision` para permitir el bloqueo de la fila al revisar. El permiso ya estaba aplicado en Supabase y se verificó; conservarlo en el SQL reproducible pendiente de subir.

Los cambios de código y documentación anteriores, incluidos AGENTS.md y este informe, se incorporaron al commit funcional publicado. El cambio local del SQL de hardening quedó fuera. Las notas de cierre se actualizan en un commit documental separado sin provocar otro despliegue.

Credenciales y material privado: están fuera de Git, en la configuración local y el archivo cifrado `.local/render-free-secrets.enc`. No copiar sus valores a este informe. Las capturas/resultados de validación están en `.local/qa/render-2026-10-15/`; los scripts privados están en `.local/`.

## Bitácora de continuidad

Las filas resumen el historial disponible, sin atribuir a esta sesión acciones realizadas en sesiones anteriores. Los detalles y sus límites se conservan en `TASK.md` y los informes enlazados.

| Fecha | Modificación / trabajo | Comprobación y punto alcanzado | Pendiente al cerrar ese paso |
| --- | --- | --- | --- |
| 2026-10-13 | Base de la aplicación, módulos, relaciones, permisos e importador | Flujos y pruebas locales documentados en TASK; PostgreSQL aún pendiente entonces | Validación visual y despliegue real |
| 2026-10-13 a 2026-10-14 | Participantes locales, asignación múltiple y formulario simplificado | Avances por persona, conservación de datos y acceso local comprobados | Publicación y revisión de datos institucionales |
| 2026-10-14 | Roles de jefatura, avisos, agenda y evidencias del equipo | Pruebas locales y flujos de navegador registrados; migraciones hasta 008 | Almacenamiento persistente y nube real |
| 2026-10-14 a 2026-10-15 | Conexiones Google/Microsoft y configuración central | Migraciones 009–010, configuración cifrada y OAuth Google local comprobados | Vinculación en la publicación y Microsoft |
| 2026-10-15, sesiones previas | Render Free y Supabase, contenedor y correcciones de PostgreSQL/Linux | Aplicación publicada; base y bucket privados preparados | Primer ingreso y revalidación remota |
| 2026-10-15, reanudación | Se encontró el avance privado más reciente y se corrigieron las notas desactualizadas | Web activa; jefatura y archivo anterior recuperados | El propietario confirmó después su ingreso |
| 2026-10-15, validación solicitada | Revisión remota de base, API, pantallas, Storage y flujo con datos ficticios; actualización de documentación | 104 pruebas backend y 75 frontend; informe técnico guardado; sin fallos en lo comprobado | BOOTSTRAP, vinculación Google, Microsoft y restauración de respaldo |
| 2026-10-15, informe de continuidad | Creación de este informe y de la regla del proyecto para actualizarlo después de cada modificación | Revisión documental, enlaces locales y `git diff --check`; sin cambios funcionales ni despliegue en este paso | Retomar por el punto 1 de Pendientes; conservar el diff local existente |
| 2026-10-15, consulta de almacenamiento | Script privado de consulta y actualización de CONTINUIDAD.md con cuotas y uso | Consulta remota de solo lectura: base principal 15,15 MB decimales; bucket privado con 3 archivos, 180 bytes. Plan Free publicado: 500 MB de base y 1 GB de Storage; fuentes oficiales contrastadas | Sin ampliación ni cambios remotos. Sigue pendiente retirar BOOTSTRAP_* y completar las conexiones externas |
| 2026-10-16, reuniones con asistentes y avisos | Migración 011 (tabla `notifications`, lectura y escritura solo para su destinatario). Al programar una reunión se eligen asistentes y reciben aviso; también al agregar asistentes después, y al cambiar fecha, lugar, título o estado (cancelación). Campana de alertas con avisos leídos al abrirlos | Local: 5 pruebas nuevas de reuniones; suite backend completa y 76 pruebas de interfaz con build correcto. **No aplicado en Supabase/Render**: requiere ejecutar la migración 011 y redeplegar | Aplicar 011 en la base de producción con respaldo previo; probar en la web con dos cuentas |
| 2026-10-16, preparación de respaldo y publicación | Revisión de 011 y del diff existente; herramientas oficiales PostgreSQL descargadas de EDB en `.local/tools/pg17`; script privado `.local/release-011.py` para copia cifrada, restauración aislada y migración condicionada al respaldo verificado | 109 pruebas backend y 76 frontend correctas; build correcto. Copia remota iniciada; no se migró ni publicó todavía. Render autenticado | Verificar copia y restauración; aplicar 011; publicar excluyendo supabase-hardening.sql; validar avisos con cuentas ficticias. Mantener servicios juntos mientras no se confirme una separación estática |
| 2026-10-16, respaldo previo a 011 | Copia consistente con pg_dump, cifrada en `.local/backups/prod-pre-011-20261016T153301Z`, más los 3 archivos de evidencia y las claves de recuperación cifradas | Restaurada en PostgreSQL local aislado: 48 tablas y 257 filas coinciden; FK restauradas y hashes de archivos correctos. Servidor temporal detenido. No se restauró sobre producción. Se corrigió un problema local de inicio de procesos en Windows | Aplicar 011 solo tras esta verificación, después publicar excluyendo el SQL de hardening. El backup es local; conservar además una copia privada externa y la clave local de recuperación |
| 2026-10-16, migración y limpieza de variables | Alembic 011 aplicado en Supabase y BOOTSTRAP_* retirados en Render con Save only | Tabla y permisos verificados; usuarios/tareas/reuniones/asistentes/evidencias conservados. 109 pruebas backend y 76 frontend y build correctos antes del envío | Commit/push y despliegue todavía pendientes; excluir hardening y validar con dos cuentas. Ver docs/publicacion-reuniones-2026-10-16.md |
| 2026-10-16, commit y push autorizados | Commit 741fdfb subido a origin/main después del respaldo verificado y 011 | Diff preparado revisado; hardening no incluido y su cambio local conservado. Ausencia de BOOTSTRAP_* comprobada tras recargar Render | Esperar despliegue y probar avisos remotos; esta actualización de continuidad queda local hasta el siguiente commit |
| 2026-10-16, despliegue y prueba final | Render desplegó 741fdfb en dep-db94fb6k1f9s73eqrfjg. Dos contextos de navegador para jefatura/integrante, lectura del aviso y apertura de reunión; cambios/cancelación verificados por HTTP | Invitación privada, lectura ajena rechazada, aviso leído al abrir, cambios y cancelación correctos. Reunión ficticia cancelada, cuenta técnica desactivada y sesión rechazada; salud y evidencia anterior correctas después del despliegue | Mantener frontend/API juntos; copia privada externa del respaldo pendiente. Guardar notas de cierre con skip render; conservar hardening local excluido |

Para cada nueva modificación, añadir una fila con fecha, cambio, archivos/servicios afectados, comprobación real y próximo paso; actualizar también el estado actual y los pendientes de este documento.
