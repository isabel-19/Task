CREATE TABLE notifications (
    id VARCHAR(36) PRIMARY KEY,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    modified_by VARCHAR(36) REFERENCES users(id) ON DELETE RESTRICT,
    revision INTEGER NOT NULL DEFAULT 1,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    kind VARCHAR(40) NOT NULL,
    entity VARCHAR(40) NOT NULL,
    record_id VARCHAR(36) NOT NULL,
    title VARCHAR(250) NOT NULL,
    message TEXT NOT NULL,
    read_at DATETIME
);
CREATE INDEX ix_notifications_user_id ON notifications(user_id);
CREATE INDEX ix_notifications_modified_by ON notifications(modified_by);
