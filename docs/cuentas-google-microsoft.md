# Vincular Google y Microsoft para presentar evidencias

La integración está implementada con OAuth por usuario, selección de documentos y una copia privada de cada archivo entregado. La conexión real requiere registrar y configurar las aplicaciones de Google Cloud y Microsoft Entra de esta instalación. No existen credenciales compartidas incluidas en el código.

## Uso

Jefatura o administración habilita los proveedores una sola vez desde **Cuentas vinculadas → Habilitar conexiones para todos los usuarios**. No se pide a cada integrante crear aplicaciones ni manejar secretos. Cualquier usuario activo con `tasks.read` y `tasks.write` puede después conectar su cuenta personal o institucional, siempre que el proveedor y su organización autoricen el acceso. Los usuarios con permiso de consulta no pueden iniciar conexiones ni adjuntar archivos. La configuración general exige `admin.write`; no basta con poder presentar evidencias.

1. Entrar con la cuenta habitual de ROADMAP OGC y abrir el botón de nube «Cuentas vinculadas» de la cabecera.
2. Pulsar Conectar cuenta en Google o Microsoft y autorizar en la página oficial del proveedor. La aplicación conserva su usuario y permisos actuales.
3. En una tarea asignada, entrar en Añadir evidencia y seleccionar Google / Microsoft.
4. Elegir un documento desde Google Picker o navegar las carpetas de OneDrive. Si acabas de vincular la cuenta en otra pestaña, pulsar Actualizar conexiones.
5. Completar descripción y porcentaje y enviar. Se conserva una copia privada para que jefatura pueda previsualizarla y revisarla con sus permisos de tarea. El original no se modifica.
6. Las evidencias mantienen el proveedor y un enlace de origen. Desvincular elimina las credenciales guardadas por la aplicación y evita nuevas consultas; las copias entregadas permanecen en el historial. La revocación completa del consentimiento también puede realizarse desde la configuración de seguridad de Google/Microsoft.

Microsoft / Outlook utiliza los archivos de OneDrive. Los adjuntos del correo deben guardarse en OneDrive o descargarse y subirse desde el equipo. No se solicitan permisos de lectura del buzón. Esta versión no explora bibliotecas independientes de SharePoint ni incorpora inicio de sesión de ROADMAP mediante Google/Microsoft.

Los documentos y presentaciones nativos de Google se exportan a PDF y las hojas a XLSX. Otros archivos mantienen su formato admitido. Rigen el tamaño configurado y las comprobaciones del almacenamiento privado. Google tiene sus propios límites para exportaciones. Consulta los [formatos oficiales de exportación](https://developers.google.com/workspace/drive/api/guides/ref-export-formats).

## Preparación local

Desde el proyecto:

```powershell
cd backend
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m alembic upgrade head
cd ..
backend/.venv/Scripts/python.exe scripts/setup-cloud-local.py
```

La migración 009 añade cuentas y estados de autorización, y procedencia de archivos. La 010 añade la configuración central cifrada. El script genera una clave Fernet en `backend/.env` si no existe; no la imprime ni reemplaza una clave anterior. Respaldar esa clave por un canal privado separado de las copias de base de datos. No incluir secretos en Git, variables VITE, capturas ni mensajes.

Configurar en el panel de jefatura las URLs que realmente usa el navegador. También pueden establecerse inicialmente en `backend/.env`. En la instancia local de revisión actual:

```dotenv
CLOUD_PUBLIC_API_URL=http://127.0.0.1:5174/api
CLOUD_FRONTEND_URL=http://127.0.0.1:5174
```

La instalación habitual de `scripts/start.ps1` usa el puerto 5173. `FRONTEND_ORIGINS` debe incluir exactamente el origen elegido. Mantener el mismo host (127.0.0.1 o localhost) durante toda la autorización para conservar la cookie de sesión. Las URLs de producción deben usar HTTPS. El prefijo `/api` puede resolverse mediante el proxy del frontend o la API pública, siempre con configuración de cookies compatible.

## Google Cloud

- Crear o seleccionar el proyecto de la oficina y habilitar Google Drive API y Google Picker API.
- Configurar la pantalla de consentimiento; definir audiencia y usuarios de prueba cuando corresponda.
- Crear un cliente OAuth de tipo Aplicación web. Registrar exactamente la redirección `CLOUD_PUBLIC_API_URL/cloud/google/callback` y el origen de la web.
- Crear una API key para Picker, restringida a las APIs y referentes necesarios. Seguir los requisitos de referentes del [ejemplo oficial de Google Picker](https://developers.google.com/workspace/drive/picker/guides/web-picker-sample).
- Introducir en el panel de configuración el ID de cliente, secreto, clave de Picker y número del mismo proyecto. Como alternativa inicial, corresponden a `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_PICKER_API_KEY` y `GOOGLE_PROJECT_NUMBER`.

Se solicita `openid email` y `https://www.googleapis.com/auth/drive.file`. El alcance de Drive permite trabajar con los archivos elegidos para la aplicación. El selector necesita un access token temporal en memoria del navegador; el refresh token y el client secret permanecen en el servidor. Referencias: [OAuth de aplicaciones web](https://developers.google.com/identity/protocols/oauth2/web-server) y [Google Picker](https://developers.google.com/workspace/drive/picker/guides/web-picker).

## Microsoft Entra

- Registrar una aplicación con el tipo de cuentas que usará la oficina. Para cuentas personales Outlook y de organizaciones, seleccionar ambos tipos y mantener `MICROSOFT_TENANT=common`; para una sola organización, usar su identificador de tenant y el registro correspondiente.
- Agregar la plataforma Web y registrar exactamente `CLOUD_PUBLIC_API_URL/cloud/microsoft/callback`. El intercambio se realiza en el servidor, por lo que esta redirección no es de tipo SPA.
- Crear una credencial de cliente y guardar su valor como `MICROSOFT_CLIENT_SECRET`; registrar el Application (client) ID como `MICROSOFT_CLIENT_ID`.
- Configurar permisos delegados `User.Read`, `Files.Read` y `offline_access`, y obtener el consentimiento exigido por la organización.

Referencias: [flujo OAuth con PKCE](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow) y [descarga autorizada de archivos](https://learn.microsoft.com/en-us/graph/api/driveitem-get-content?view=graph-rest-1.0).

Los cambios guardados desde el panel se aplican inmediatamente a todos los usuarios, sin reiniciar. El servidor conserva esta configuración cifrada y tiene prioridad sobre las variables de entorno. Los secretos guardados no se muestran de nuevo: dejar los campos de contraseña vacíos los conserva. Solo los cambios hechos directamente en `.env` requieren reiniciar la API; después de guardar la configuración central deben hacerse los cambios desde el panel.

Cambiar el ID de una aplicación o el directorio Microsoft desvincula las cuentas de ese proveedor para que sus propietarios autoricen el nuevo registro. Rotar un secreto conservando el mismo ID no borra las conexiones. Cualquier guardado cancela autorizaciones que aún estuvieran abiertas; sus usuarios pueden comenzar otra vez. Las evidencias ya entregadas permanecen. La bitácora registra quién cambió la configuración y los nombres de los campos, sin valores de credenciales.

Cuentas vinculadas solo habilita Conectar cuando la configuración está completa. Si el proveedor rechaza la cuenta o la autorización, revisar el registro de la aplicación, la audiencia, la redirección exacta, los permisos y la política de la organización. No activar una configuración ficticia para aparentar una conexión.

## Verificación

Las pruebas locales comprueban estado de un solo uso ligado al usuario y sesión, PKCE, cifrado, renovación, separación entre usuarios, desvinculación, selección y copia privada, y aviso a jefatura. Las llamadas OAuth/Drive/Graph se verifican con respuestas simuladas: no acreditan autorización real de una cuenta institucional. La verificación con proveedores reales queda pendiente hasta disponer de las aplicaciones OAuth y autorizar las cuentas en el navegador.

Validación del 14 de octubre: 89 pruebas de servidor y 72 de interfaz correctas y compilación de producción correcta. La configuración central se revisó en navegador a 1440, 390 y 320 px sin desbordamiento horizontal: jefatura pudo guardar y recuperar la configuración, mientras un integrante no vio el panel y recibió 403 al solicitar su API. Se aplicó la migración 010 a las bases de trabajo, revisión y QA después de respaldarlas, verificando integridad y conservación de columnas/filas anteriores. En esa validación todavía no había credenciales OAuth ni cuentas reales conectadas.

## Activación local de Google, 15 de octubre de 2026

Se creó el proyecto Google Cloud de ROADMAP OGC con la cuenta proporcionada por el propietario. El propietario inició sesión y aceptó personalmente las condiciones y la política de datos. Tras su autorización explícita se crearon el cliente OAuth web y una clave de Picker restringida a Google Drive/Google Picker y a los referentes de la instancia local y `docs.google.com` que requiere el selector.

Las credenciales se guardaron cifradas en la configuración central de la instancia de revisión `http://127.0.0.1:5174`, con respaldo previo de la base. El registro de instalación utiliza un actor de sistema, sin atribuirlo a una cuenta ficticia. No se guardaron secretos en el código, la documentación ni las salidas de herramientas. El servidor confirmó que Google está configurado; Microsoft sigue pendiente.

Google permanece en estado **Prueba** y solo se añadió la cuenta facilitada por el propietario a sus usuarios de prueba. Otros usuarios necesitan incorporarse a esa lista o completar la configuración de marca y publicación para uso general. No se publicaron la aplicación ni documentos en Google y no se configuró facturación.

La cuenta facilitada por el propietario se vinculó después de su autorización en Google. El primer retorno falló porque la API local se ejecutaba sin salida de red desde el entorno restringido. Tras reiniciar el mismo servicio con acceso autorizado, Google completó el intercambio y ROADMAP confirmó la cuenta conectada. No se cambiaron los permisos concedidos.

El selector oficial se abrió con esa cuenta real y mostró las vistas Todos los archivos, Compartidos conmigo y unidades compartidas. Se comprobó que la pestaña de compartidos se abre sin errores. No se seleccionó ni copió ningún documento real durante esta verificación.

## Archivos propios y compartidos de cada usuario

La cuenta que registra el proyecto Google no filtra las cuentas que pueden vincularse. Cada usuario autorizado de ROADMAP conserva su propia conexión Google. Una vez habilitado para ese usuario en Google, el selector muestra archivos accesibles de su cuenta, incluidos los compartidos con ella. No necesita ser propietario. Las unidades compartidas usan el soporte `supportsAllDrives` de Drive.

Desde Cuentas vinculadas, **Explorar y previsualizar** permite elegir un documento y consultar su contenido antes de crear una evidencia. En Añadir evidencia también aparece **Previsualizar** después de seleccionar un archivo de Google. La vista consulta el documento con las credenciales de la persona, valida el formato y entrega el contenido sin caché; no crea tareas, evidencias ni archivos persistentes. La copia privada para jefatura solo se guarda al enviar una evidencia a revisión.

La aplicación respeta la prohibición de descarga/copia que establezca el propietario. En esos casos mantiene **Abrir en Google** para consultar el original con la cuenta y las restricciones del proveedor. El acceso a un enlace no permite eludir permisos de Drive. La previsualización admite los mismos formatos que las evidencias; Google Docs/presentaciones se exportan a PDF y hojas de cálculo a XLSX cuando está permitido.

Las pruebas comprueban que otro usuario no puede usar la conexión ajena para previsualizar, que una persona integrante puede consultar su propio documento seleccionado, que los compartidos no se filtran por propietario y que una restricción de copia se respeta. Resultado actualizado: 92 pruebas backend, 75 frontend, compilación y diff --check correctos. La lectura de un documento real queda pendiente de que su titular elija uno para la prueba; las comprobaciones de contenido se hicieron con respuestas de proveedor simuladas.

**Disponibilidad para otros Gmail:** el registro de Google sigue en modo Prueba. La consola mantiene Publicar app deshabilitado e indica completar la información de marca. La configuración aún no tiene dirección pública de la aplicación ni enlaces públicos a sus políticas. No se inventaron esos enlaces ni se publicó la aplicación. Hasta completar ese paso, los correos adicionales deben incorporarse a los usuarios de prueba; no se afirma disponibilidad general para cualquier Gmail.
