ALTER TABLE roadmap.projects ADD COLUMN group_key VARCHAR(80);
CREATE UNIQUE INDEX uq_projects_group_key ON roadmap.projects (group_key);
ALTER TABLE roadmap.tasks ADD COLUMN office VARCHAR(160);
