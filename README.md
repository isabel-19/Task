# ROADMAP OGC · UNAJMA

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

Para el flujo actualizado de jefe/integrantes, tareas grupales y evidencias, consulta [roles y avances](docs/roles-y-avances.md) y [el manual](docs/manual.md). La vista predeterminada de tareas es personal; jefatura puede elegir «Equipo».

El registro de participantes del Excel y sus accesos locales se explica en [participantes](docs/participantes.md). En la instalación local ya aparecen en Tareas → Participantes del equipo y en los selectores de asignación.

La asignación usa un formulario reducido con temática, actividad, responsable, apoyo y plazo. Oficina y observaciones son opcionales; los desplegables siguen el libro. Consulta [asignación simple](docs/asignacion-simple.md).
