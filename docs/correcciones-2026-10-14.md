# Correcciones y actualización visual — 14 de octubre de 2026

Se retomaron los cambios locales relacionados con los 12 hallazgos de la [auditoría del 13 de octubre](auditoria-2026-10-13.md). Se conservan las correcciones funcionales y se añadió un sistema visual compartido para acceso, navegación, dashboard, módulos, formularios y fichas.

## Cambios funcionales conservados

| Hallazgo | Cambio en el código |
| --- | --- |
| H01 | Paginación sincronizada entre `ModuleView` y `EntityTable`, conservando el total de registros. |
| H02 | Sincronización de la búsqueda al cambiar la consulta sobre la misma ruta. |
| H03 | Filtro de reuniones que incluye todas las horas del último día y rechaza rangos invertidos. |
| H04 | Contenedores del login con ancho adaptable y sin un mínimo superior al viewport. |
| H05 | Búsquedas en relaciones por nombres visibles, conservando el alcance de tareas. |
| H06 | Mensajes de validación en español en API, acciones e importación. |
| H07 | Etiquetas comprensibles para campos internos en tablas y fichas. |
| H08 | Fechas de calendario del Gantt interpretadas sin desplazamiento por zona horaria. |
| H09 | Instantes de auditoría serializados con zona UTC; fechas de calendario conservadas. |
| H10 | Exportación de metadatos de importaciones, limitada por los permisos existentes. |
| H11 | API a través del proxy de desarrollo para mantener el mismo origen en `localhost` y `127.0.0.1`. |
| H12 | Ajuste de texto largo y abreviación visual del hash, conservando su valor completo. |

## Actualización visual

- Menú verde profundo con selección visible, fondo cálido y superficies claras.
- Dashboard con bienvenida personalizada, fecha e ilustración de ruta hecha en SVG.
- Tarjetas con acentos por estado, números más legibles y una jerarquía más clara.
- Texto, etiquetas y estados con mayor tamaño y contraste en módulos, tablas y formularios.
- Login con el mismo lenguaje visual e indicaciones de ayuda para el usuario, sin rutas técnicas locales.
- Adaptación de la cabecera, tarjetas y formularios a pantallas estrechas; foco de teclado visible y respeto por la preferencia de movimiento reducido.

El tema se concentra en `frontend/src/theme.css`. La ilustración reutilizable está en `frontend/src/components/RouteMotif.vue` y no requiere servicios ni fuentes externas.

## Verificación y límites

- Backend: 48 pruebas correctas, incluyendo fechas, búsquedas relacionadas, permisos, exportaciones y flujos de tareas, documentos, evidencias e importación.
- Frontend: 33 pruebas correctas después de los cambios visuales.
- Compilación de producción: correcta.
- Revisión de espacios y conflictos con `git diff --check`: correcta.
- Los registros de navegador del 13 de octubre están en `.local/browser-audit-fixes/`. Son evidencia histórica de las correcciones funcionales, **no** una revisión del nuevo tema.
- Se preparó una copia local de SQLite y servidores de revisión en 5174/8001, con artefactos en `.local/browser-audit-2026-10-14/`.
- La nueva revisión visual en Chrome está pendiente: el lanzamiento de Chrome requiere un permiso que no se completó. `codex mcp list` muestra Playwright habilitado, pero sus herramientas no están expuestas en esta conversación; el navegador integrado no encontró conexiones activas.

No se ejecutaron pruebas nuevas de navegador del tema, PostgreSQL/Supabase ni despliegue público. Los cambios permanecen locales, sin commit ni publicación en GitHub.
