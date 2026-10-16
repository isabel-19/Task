# Verificación de Render y Supabase — 15 de octubre de 2026

La aplicación publicada en https://roadmap-ogc.onrender.com superó las comprobaciones siguientes. Se distinguieron las pruebas sobre el alojamiento real de las suites locales. No se modificó el código funcional ni la configuración del alojamiento durante esta revisión.

## Alojamiento y API reales

- Salud HTTPS: `status=ok`, `environment=production`, `demo=false`, `database=postgresql`.
- Ingreso y cierre de sesión de jefatura correctos. Cookie con Secure, HttpOnly, SameSite y ruta `/api` comprobadas.
- Los 40 recursos de la API y otras 10 consultas (catálogos, dashboard, avisos, participantes, cuentas, configuración, opciones de archivos, sesión y dos reportes CSV) respondieron correctamente.
- Rechazo del acceso anónimo a tareas, usuarios, dashboard y configuración; rechazo de operaciones sin CSRF y con origen ajeno.
- Rutas `.env`, base local y archivos estáticos inexistentes no expuestas; JavaScript y CSS publicados disponibles.

## PostgreSQL real

La revisión directa utilizó transacciones de solo lectura, sin ejecutar migraciones ni cambiar permisos o contraseñas.

| Comprobación | Resultado |
| --- | --- |
| Conexiones de migración y aplicación | TLS activo en ambas |
| Migración instalada | `010` |
| Tablas del modelo revisadas | 47, con todas sus columnas presentes |
| Restricciones FK/CHECK validadas | 146 |
| Relaciones FK comprobadas contra los datos | 128; cero registros huérfanos |
| Índices inválidos o incompletos | 0 |
| Conexiones bloqueadas en el momento de la consulta | 0 |
| Tamaño de la base en ese momento | 14,45 MB |
| Esquema `roadmap` | Sin USAGE para `anon` ni `authenticated` |
| Usuario de ejecución | `roadmap_api`, sin superusuario, creación de bases, roles ni objetos en el esquema |
| Historial y auditoría | Sin UPDATE general en las tablas inmutables |
| Bloqueo de versiones de evidencia | UPDATE permitido solamente sobre `revision`; URL protegida |
| Configuración de Google almacenada | Cifrada; descifrado y origen público correctos |

El permiso de columna sobre `evidence_versions.revision` ya estaba aplicado en Supabase y figura en el cambio local pendiente de `database/supabase-hardening.sql`. Esta revisión verificó el permiso existente; no lo volvió a aplicar.

## Flujo real con datos ficticios

Se creó un integrante técnico con correo del dominio reservado `example.invalid` y una tarea identificada como ficticia. Se verificó asignación → ingreso del integrante → carga de TXT → descarga y previsualización → aviso a jefatura → revisión → cierre → retirada del aviso. El integrante no pudo revisar su propia entrega y la descarga anónima fue rechazada.

La tarea quedó cerrada y la cuenta técnica desactivada. Se conservaron la evidencia y el historial para comprobar persistencia. Una nueva conexión HTTPS recuperó la tarea cerrada y el archivo con su SHA-256 correcto. **No se provocó un reinicio de Render** durante esta revisión.

Una prueba independiente de Supabase Storage verificó bucket privado, carga y lectura íntegra, rechazo de URL pública y borrado del objeto técnico temporal.

## Navegador y suites locales

- Se abrieron las 11 pantallas principales y Cuentas vinculadas con la sesión de jefatura: sin excepciones JavaScript ni respuestas HTTP de error observadas durante esas cargas.
- En Tareas, Todas las tareas mostró los registros ficticios cerrados y el botón Previsualizar abrió el contenido guardado en Supabase.
- Lista de tareas inspeccionada en escritorio y móvil. A 390 px, una vez terminado el ajuste del diseño, el documento midió 390 px sin desbordamiento horizontal.
- Backend: **104 pruebas correctas**. Incluyen reglas de los módulos, permisos, migraciones, archivos, integraciones simuladas y arranque. Estas pruebas usan entornos aislados; no sustituyen las comprobaciones remotas descritas arriba.
- Interfaz: **75 pruebas correctas**, en 11 archivos.

Las suites mostraron avisos de deprecación de dependencias del cliente de pruebas, sin fallos.

Los resultados JSON y capturas locales están en `.local/qa/render-2026-10-15/`, fuera de Git. Los scripts de validación leen las credenciales cifradas y no las incluyen en los resultados.

## Pendientes y límites de esta revisión

- Google está configurado, pero la cuenta de jefatura aparece sin vincular en la web. Falta la autorización personal y la prueba real con Drive en este dominio.
- Microsoft todavía no está habilitado por administración.
- El panel de Render conserva `BOOTSTRAP_EMAIL`, `BOOTSTRAP_NAME` y `BOOTSTRAP_PASSWORD`. Retirarlos después del primer ingreso sigue pendiente; no se editaron variables durante esta revisión.
- No se probó restaurar un backup de PostgreSQL, reiniciar el servicio ni ejecutar operaciones de escritura reales de cada uno de los demás módulos. Las suites locales cubren sus reglas y todas sus consultas remotas revisadas funcionaron.

El resultado acredita las comprobaciones realizadas; no constituye una garantía de disponibilidad futura del alojamiento gratuito ni de integraciones externas todavía sin vincular.
