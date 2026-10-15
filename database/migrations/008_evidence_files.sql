CREATE TABLE IF NOT EXISTS roadmap.evidence_files (
    id VARCHAR(36) PRIMARY KEY,
    evidence_version_id VARCHAR(36) NOT NULL UNIQUE REFERENCES roadmap.evidence_versions(id) ON DELETE RESTRICT,
    storage_key VARCHAR(64) NOT NULL UNIQUE,
    file_name VARCHAR(250) NOT NULL,
    content_type VARCHAR(120) NOT NULL,
    byte_size INTEGER NOT NULL CHECK (byte_size > 0),
    sha256 VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    modified_by VARCHAR(36) REFERENCES roadmap.users(id) ON DELETE RESTRICT,
    revision INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS ix_evidence_files_evidence_version_id ON roadmap.evidence_files(evidence_version_id);
CREATE INDEX IF NOT EXISTS ix_evidence_files_modified_by ON roadmap.evidence_files(modified_by);
