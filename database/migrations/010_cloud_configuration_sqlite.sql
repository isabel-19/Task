CREATE TABLE cloud_configuration (
    id VARCHAR(36) PRIMARY KEY CHECK (id = 'application'),
    settings_ciphertext TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    modified_by VARCHAR(36) REFERENCES users(id) ON DELETE RESTRICT,
    revision INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX ix_cloud_configuration_modified_by ON cloud_configuration(modified_by);
