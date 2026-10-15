ALTER TABLE documents ADD COLUMN axis_id VARCHAR(36) REFERENCES axes(id) ON DELETE RESTRICT;
CREATE INDEX ix_documents_axis_id ON documents(axis_id);
UPDATE documents SET axis_id = (SELECT projects.axis_id FROM projects WHERE projects.id = documents.project_id) WHERE project_id IS NOT NULL;
