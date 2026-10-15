ALTER TABLE roadmap.documents ADD COLUMN axis_id VARCHAR(36) REFERENCES roadmap.axes(id) ON DELETE RESTRICT;
CREATE INDEX ix_roadmap_documents_axis_id ON roadmap.documents(axis_id);
UPDATE roadmap.documents SET axis_id = projects.axis_id FROM roadmap.projects WHERE projects.id = documents.project_id;
