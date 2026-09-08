"""
SQLite database schema DDL definitions for Fact Knowledge Layer.
"""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    document_type TEXT DEFAULT 'unknown',
    page_count INTEGER NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    file_hash TEXT NOT NULL,
    status TEXT DEFAULT 'uploaded',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pages (
    page_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    word_count INTEGER NOT NULL,
    FOREIGN KEY(document_id) REFERENCES documents(document_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS facts (
    fact_id TEXT PRIMARY KEY,
    source_document_id TEXT NOT NULL,
    source_document_name TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    raw_value TEXT NOT NULL,
    raw_unit TEXT,
    period TEXT,
    scope TEXT,
    original_value TEXT,
    normalized_value REAL,
    original_unit TEXT,
    normalized_unit TEXT,
    is_numerical INTEGER DEFAULT 1,
    evidence_text TEXT NOT NULL,
    confidence REAL DEFAULT 0.9,
    extraction_method TEXT DEFAULT 'deterministic',
    embedding_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(source_document_id) REFERENCES documents(document_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS fact_comparisons (
    comparison_id TEXT PRIMARY KEY,
    fact_a_id TEXT NOT NULL,
    fact_b_id TEXT NOT NULL,
    relationship TEXT NOT NULL,
    confidence REAL DEFAULT 0.9,
    reason TEXT NOT NULL,
    differences_json TEXT,
    evidence_a_json TEXT NOT NULL,
    evidence_b_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(fact_a_id) REFERENCES facts(fact_id) ON DELETE CASCADE,
    FOREIGN KEY(fact_b_id) REFERENCES facts(fact_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pages_doc ON pages(document_id);
CREATE INDEX IF NOT EXISTS idx_facts_doc ON facts(source_document_id);
CREATE INDEX IF NOT EXISTS idx_facts_predicate ON facts(predicate);
CREATE INDEX IF NOT EXISTS idx_facts_period ON facts(period);
CREATE INDEX IF NOT EXISTS idx_comparisons_pair ON fact_comparisons(fact_a_id, fact_b_id);
CREATE INDEX IF NOT EXISTS idx_comparisons_rel ON fact_comparisons(relationship);
"""
