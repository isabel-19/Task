CREATE TABLE roadmap.cloud_accounts (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES roadmap.users(id) ON DELETE RESTRICT,
    provider VARCHAR(20) NOT NULL CHECK (provider IN ('google','microsoft')),
    subject VARCHAR(256) NOT NULL,
    account_label VARCHAR(254) NOT NULL,
    token_ciphertext TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    modified_by VARCHAR(36) REFERENCES roadmap.users(id) ON DELETE RESTRICT,
    revision INTEGER NOT NULL DEFAULT 1,
    UNIQUE(user_id, provider)
);
CREATE INDEX ix_cloud_accounts_user_id ON roadmap.cloud_accounts(user_id);
CREATE INDEX ix_cloud_accounts_modified_by ON roadmap.cloud_accounts(modified_by);
CREATE TABLE roadmap.cloud_oauth_states (
    state_hash VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES roadmap.users(id) ON DELETE RESTRICT,
    provider VARCHAR(20) NOT NULL,
    session_hash VARCHAR(64) NOT NULL,
    verifier_ciphertext TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL
);
CREATE INDEX ix_cloud_oauth_states_user_id ON roadmap.cloud_oauth_states(user_id);
ALTER TABLE roadmap.evidence_files ADD COLUMN source_provider VARCHAR(20);
ALTER TABLE roadmap.evidence_files ADD COLUMN source_item_id VARCHAR(256);
ALTER TABLE roadmap.evidence_files ADD COLUMN source_url TEXT;
