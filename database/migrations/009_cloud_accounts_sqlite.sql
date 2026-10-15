CREATE TABLE cloud_accounts (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    provider VARCHAR(20) NOT NULL CHECK (provider IN ('google','microsoft')),
    subject VARCHAR(256) NOT NULL,
    account_label VARCHAR(254) NOT NULL,
    token_ciphertext TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    modified_by VARCHAR(36) REFERENCES users(id) ON DELETE RESTRICT,
    revision INTEGER NOT NULL DEFAULT 1,
    UNIQUE(user_id, provider)
);
CREATE INDEX ix_cloud_accounts_user_id ON cloud_accounts(user_id);
CREATE INDEX ix_cloud_accounts_modified_by ON cloud_accounts(modified_by);
CREATE TABLE cloud_oauth_states (
    state_hash VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    provider VARCHAR(20) NOT NULL,
    session_hash VARCHAR(64) NOT NULL,
    verifier_ciphertext TEXT NOT NULL,
    expires_at DATETIME NOT NULL
);
CREATE INDEX ix_cloud_oauth_states_user_id ON cloud_oauth_states(user_id);
ALTER TABLE evidence_files ADD COLUMN source_provider VARCHAR(20);
ALTER TABLE evidence_files ADD COLUMN source_item_id VARCHAR(256);
ALTER TABLE evidence_files ADD COLUMN source_url TEXT;
