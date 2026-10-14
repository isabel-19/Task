ALTER TABLE projects ADD COLUMN group_key VARCHAR(80);
CREATE UNIQUE INDEX uq_projects_group_key ON projects (group_key);
ALTER TABLE tasks ADD COLUMN office VARCHAR(160);
