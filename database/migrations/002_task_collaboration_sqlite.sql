ALTER TABLE tasks ADD COLUMN created_by VARCHAR(36) REFERENCES users(id) ON DELETE RESTRICT;

CREATE INDEX ix_tasks_created_by ON tasks (created_by);

ALTER TABLE task_assignments ADD COLUMN assigned_by VARCHAR(36) REFERENCES users(id) ON DELETE RESTRICT;

CREATE INDEX ix_task_assignments_assigned_by ON task_assignments (assigned_by);

ALTER TABLE task_updates ADD COLUMN evidence_version_id VARCHAR(36) REFERENCES evidence_versions(id) ON DELETE RESTRICT;

CREATE INDEX ix_task_updates_evidence_version_id ON task_updates (evidence_version_id);

CREATE TABLE task_update_reviews (
	task_update_id VARCHAR(36) NOT NULL, 
	reviewer_id VARCHAR(36) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	note TEXT NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (task_update_id), 
	FOREIGN KEY(reviewer_id) REFERENCES users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES users (id) ON DELETE RESTRICT, 
	CONSTRAINT task_review_status CHECK (status IN ('validada','observada')), 
	FOREIGN KEY(task_update_id) REFERENCES task_updates (id) ON DELETE RESTRICT
);

CREATE INDEX ix_task_update_reviews_modified_by ON task_update_reviews (modified_by);

CREATE INDEX ix_task_update_reviews_reviewer_id ON task_update_reviews (reviewer_id);

CREATE INDEX ix_task_update_reviews_task_update_id ON task_update_reviews (task_update_id);

INSERT INTO permissions (id, name, created_at, updated_at, revision) VALUES ('c44d2424-32be-49cd-9d0d-137d23e6ab7c','tasks.supervise',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,1), ('b0c7a73f-59b9-42c4-850e-bb6c8d07ed86','tasks.team_read',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,1);

INSERT INTO role_permissions (id, role_id, permission_id, created_at, updated_at, revision) SELECT lower(hex(randomblob(16))), r.id, p.id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1 FROM roles r CROSS JOIN permissions p WHERE (r.name IN ('administrador','jefatura') AND p.name='tasks.supervise') OR (r.name='consulta_auditoria' AND p.name='tasks.team_read');

UPDATE tasks SET created_by=(SELECT actor_id FROM audit a WHERE a.entity='tasks' AND a.record_id=tasks.id AND a.action IN ('create','from_agreement','recurrence','import') ORDER BY a.created_at LIMIT 1);

UPDATE task_assignments SET assigned_by=(SELECT actor_id FROM audit a WHERE a.entity='task-assignments' AND a.record_id=task_assignments.id AND a.action='create' ORDER BY a.created_at LIMIT 1);
