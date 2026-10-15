INSERT INTO roadmap.role_permissions (id, role_id, permission_id, created_at, updated_at, modified_by, revision)
SELECT md5(random()::text || clock_timestamp()::text), chief.id, granted.permission_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, granted.modified_by, 1
FROM roadmap.roles chief
JOIN roadmap.roles admin_role ON admin_role.name = 'administrador'
JOIN roadmap.role_permissions granted ON granted.role_id = admin_role.id
WHERE chief.name = 'jefatura'
AND NOT EXISTS (SELECT 1 FROM roadmap.role_permissions present WHERE present.role_id = chief.id AND present.permission_id = granted.permission_id);
