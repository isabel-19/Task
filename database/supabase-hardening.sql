-- Aplicar con el rol de migración, después de 010, en una instancia DE PRUEBA.
-- El backend conecta como roadmap_api; establecer su contraseña fuera de Git.
-- Verificar estos permisos antes de conectar Supabase. Este script no ha sido ejecutado aquí.
CREATE ROLE roadmap_api LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
REVOKE ALL ON SCHEMA roadmap FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA roadmap FROM PUBLIC;
GRANT USAGE ON SCHEMA roadmap TO roadmap_api;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA roadmap TO roadmap_api;
REVOKE UPDATE ON roadmap.audit, roadmap.task_updates, roadmap.task_update_reviews, roadmap.closure_approvals,
  roadmap.case_events, roadmap.evidence_versions, roadmap.document_versions,
  roadmap.evidence_validations, roadmap.deliverable_reviews, roadmap.import_sources FROM roadmap_api;
GRANT DELETE ON roadmap.sessions, roadmap.login_attempts, roadmap.user_roles, roadmap.role_permissions TO roadmap_api;
GRANT DELETE ON roadmap.cloud_accounts, roadmap.cloud_oauth_states TO roadmap_api;
REVOKE ALL ON roadmap.alembic_version FROM roadmap_api;
-- Supabase crea anon y authenticated; estos comandos son exclusivos de ese entorno.
REVOKE ALL ON SCHEMA roadmap FROM anon, authenticated;
REVOKE ALL ON ALL TABLES IN SCHEMA roadmap FROM anon, authenticated;
-- No incluir roadmap en los esquemas expuestos de la Data API de Supabase.
-- Las políticas por acción y responsabilidad viven en FastAPI.
