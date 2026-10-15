# Participantes del ROADMAP

El usuario autorizó registrar los participantes del libro local después de la revisión de estructura. La importación se ejecuta solo en esta instalación; el Excel original no se modifica. No se publicaron sus datos ni se importaron tareas, documentos, evidencias o conformidades institucionales.

## Lectura y registro

Se revisan las columnas de participantes, responsable, apoyo, elaborado por y TEAM OGC de las hojas, además de nombres de personas en Entregables OS. Los encabezados se resuelven por su texto, no por una posición fija; por ejemplo, Responsable está en H en TASK/PAINS. Se separan nombres agrupados por barras, comas, punto y coma, saltos de línea o la conjunción «y». Los grupos como «Todo el equipo» y las organizaciones no se convierten en personas.

Se unifican únicamente mayúsculas, espacios y tildes. La similitud de escritura señala posibles variantes, pero no fusiona identidades. Las formas originales, hoja, celda, fila y encabezado se guardan por persona en `import_batches.preview`, junto con el UUID de usuario. El SHA-256 y una copia íntegra del XLSX respaldan la procedencia. Los nombres reales, fuentes y accesos quedan en la base local, `backend/storage` y `.local`, todos ignorados por Git.

La operación es idempotente por hash del archivo y tipo de importación. Una nueva versión reutiliza las cuentas por la identidad ya registrada, identificador local o nombre normalizado inequívoco; no cambia contraseñas ni roles de usuarios existentes.

## Acceso y uso

El libro no suministra correos institucionales en las columnas utilizadas. Las cuentas nuevas usan identificadores técnicos con el dominio reservado `@participantes.invalid`, contraseñas aleatorias y rol integrante. No se presentan estos identificadores como direcciones de contacto. Las contraseñas no se envían por correo ni aparecen en la API o la bitácora.

Los accesos están en `.local/participantes-accesos.txt`; su versión estructurada es `.local/participants-access.json`. Introduce el identificador completo y su contraseña en el formulario de inicio de sesión. Conserva esos archivos en esta instalación; no los publiques. Administración puede sustituir el identificador por un correo institucional y renovar la contraseña cuando se confirme la identidad.

En **Tareas → Asignar tarea**, busca el nombre en **Responsable**. La tarea aparece en **Mis tareas** de la persona seleccionada. El jefe puede revisarla en **Tareas que asigné** o **Todas las tareas**. La identidad del jefe entre los nombres del libro debe confirmarse: la importación no deduce ese privilegio a partir de nombres o de la hoja temática Roles.

El aviso de la aplicación distingue la instalación con participantes del Excel de una demostración compuesta únicamente por registros ficticios. Las cuentas y tareas de demostración anteriores se conservan.

## Repetir desde el directorio del proyecto

```powershell
& .\backend\.venv\Scripts\python.exe -X utf8 .\scripts\import-roadmap-participants.py --source 'C:\ruta\ROADMAP OGC 2026 v2.xlsx'
```

Ese comando solo prepara la lectura. Para aplicar la carga autorizada agrega `--apply`, después de guardar un respaldo con `scripts/backup-demo.py`. Repetir el mismo archivo no crea cuentas adicionales ni cambia contraseñas.
