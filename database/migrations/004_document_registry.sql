CREATE TABLE roadmap.document_sequences (
    series VARCHAR(40) NOT NULL,
    year INTEGER NOT NULL,
    last_number INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (series, year),
    CONSTRAINT document_sequence_nonnegative CHECK (last_number >= 0)
);
