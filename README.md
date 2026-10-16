# ROADMAP OGC · UNAJMA

Para retomar otra sesión, leer primero el [informe de continuidad](CONTINUIDAD.md): resume lo realizado, el estado publicado, las pruebas y el siguiente paso. Por petición del propietario, se actualiza después de cada modificación conforme a [AGENTS.md](AGENTS.md).

Aplicación interna de planificación, registro documental y trazabilidad con Vue 3 + Quasar, FastAPI y modelo relacional portable a PostgreSQL/Supabase. El repositorio incluye código y una demostración con datos ficticios. Las decisiones de flujo se validan en la API.

La base local, los participantes importados, los Excel originales, las contraseñas y la configuración privada no se versionan. Al instalar en otro equipo se genera una nueva demostración; los participantes y catálogos se cargan desde una copia privada del Excel siguiendo las guías de importación.

## Inicio local (PowerShell)

Requisitos: Node 20.19+ o 22.12+, Python 3.11+, PostgreSQL para el entorno institucional. Esta máquina usa Node 24 y Python 3.14. Para una demostración sin PostgreSQL se permite SQLite con claves foráneas activas; no sustituye la verificación de Supabase.

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
Copy-Item .env.example backend/.env
cd backend
.venv/Scripts/python.exe -m app.seed
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

En otra terminal:

```powershell
cd frontend
npm install
npm run dev
```

Abrir http://127.0.0.1:5173. El instalador de demostración genera una contraseña aleatoria y la guarda en `.local/demo-access.txt` (ignorado por Git). Todas las cuentas de demostración pertenecen al dominio reservado `example.invalid`. No hay contraseña predeterminada. Los registros se persisten en `backend/roadmap-demo.db`.

Con las dependencias ya instaladas, iniciar ambos servicios desde la carpeta raíz con `./scripts/start.ps1` y detenerlos con `./scripts/stop.ps1`. Se ejecutan en segundo plano, con registros en `.local`, sin ventanas adicionales. El instalador aplica Alembic antes de cargar la demostración y no reemplaza datos existentes.

## PostgreSQL

Instalar `backend/requirements-postgres.txt`, configurar `DATABASE_URL` en `backend/.env` con `postgresql+psycopg://...?...sslmode=require` y ejecutar desde backend:

```powershell
.venv/Scripts/python.exe -m alembic upgrade head
```

El SQL reproducible está en `database/migrations/001_initial.sql`. Los cambios posteriores necesitan una nueva migración. La API no crea tablas al iniciar. La cuenta de servicio debe ser restringida al esquema y usarse solo desde el backend. Nunca poner la clave de servicio en `VITE_*`.

## Validación

```powershell
cd backend
.venv/Scripts/python.exe -m unittest discover -s tests -v
cd ../frontend
npm test
npm run build
```

Documentación: [navegación](docs/navegacion.md), [modelo de datos](docs/modelo-datos.md), [manual](docs/manual.md), [operación](docs/operacion.md), [importación](docs/importacion.md), [estado y pendientes](TASK.md). El registro de verificaciones distingue las pruebas locales de la validación PostgreSQL y del despliegue.

Registro Digital permite pegar el enlace al crear o editar documentos y asignar correlativos por tipo y año. Consulta [enlaces y numeración](docs/registro-digital.md) para continuar las series de un registro existente.

Para el flujo actualizado de jefe/integrantes, tareas grupales y evidencias, consulta [roles y avances](docs/roles-y-avances.md) y [el manual](docs/manual.md). La vista predeterminada de tareas es personal; jefatura puede elegir «Equipo».

El registro de participantes del Excel y sus accesos locales se explica en [participantes](docs/participantes.md). En la instalación local aparecen en el selector de responsable al asignar una tarea.

Tareas y responsables permite asignar a una o varias personas: tarea, personas asignadas, fecha límite e instrucciones opcionales. El responsable consulta «Mis tareas» y añade sus avances y enlaces desde «Añadir evidencia». El envío queda pendiente de revisión por otra persona de jefatura. Lista y agenda semanal permiten abrir documentos directamente; la ficha separa entrega y respuesta. Consulta [asignación simple](docs/asignacion-simple.md) y [agenda, evidencias y azul institucional](docs/agenda-evidencias-azul.md).

También se pueden adjuntar archivos del equipo, hasta 20 MB por envío: PDF, imágenes PNG/JPG/WEBP, DOCX, XLSX, TXT y CSV. El previsualizador integrado permite leer PDF, imágenes y el contenido de Word/Excel; conserva la descarga del original. Requiere instalar las dependencias y aplicar Alembic hasta 008. Consulta [uso](docs/manual.md) y [almacenamiento privado y respaldo](docs/operacion.md).

Google y Microsoft se vinculan por usuario desde Cuentas vinculadas. Jefatura habilita una sola vez las aplicaciones OAuth desde el panel de configuración general; después, cualquier usuario con permiso para trabajar en tareas puede autorizar su propia cuenta. La selección usa Google Picker o los archivos de OneDrive; la entrega conserva una copia privada para revisión. Requiere Alembic hasta 010 y registrar las aplicaciones externas antes de conectar cuentas reales. Consulta la [activación de Google y Microsoft](docs/cuentas-google-microsoft.md).

La aplicación está publicada en https://roadmap-ogc.onrender.com con Render Free para la interfaz/API y Supabase Free para PostgreSQL y evidencias privadas. Se verificaron salud de producción, ingreso de jefatura y recuperación de un archivo privado de prueba. Consulta el [estado de Render y los siguientes pasos](docs/render-gratuito.md), incluida la comprobación pendiente de las variables temporales `BOOTSTRAP_*` en el panel.
