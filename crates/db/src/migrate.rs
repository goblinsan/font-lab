use sqlx::SqlitePool;

pub async fn run_migrations(pool: &SqlitePool) -> Result<(), sqlx::Error> {
    sqlx::raw_sql(SCHEMA).execute(pool).await?;
    Ok(())
}

const SCHEMA: &str = r#"
-- Font Samples
CREATE TABLE IF NOT EXISTS font_samples (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    filename        TEXT NOT NULL UNIQUE,
    original_filename TEXT NOT NULL,
    slug            TEXT UNIQUE,
    font_name       TEXT,
    font_category   TEXT,
    style           TEXT,
    genre           TEXT,
    theme           TEXT,
    era             TEXT,
    provenance      TEXT,
    confidence      REAL,
    notes           TEXT,
    source          TEXT,
    restoration_notes TEXT,
    tags            TEXT NOT NULL DEFAULT '[]',
    file_size       INTEGER,
    content_type    TEXT,
    uploaded_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    -- Extended taxonomy
    origin_context      TEXT,
    source_type         TEXT,
    restoration_status  TEXT,
    rights_status       TEXT,
    rights_notes        TEXT,
    completeness        REAL,
    moods               TEXT NOT NULL DEFAULT '[]',
    use_cases           TEXT NOT NULL DEFAULT '[]',
    construction_traits TEXT NOT NULL DEFAULT '[]',
    visual_traits       TEXT NOT NULL DEFAULT '[]',

    -- Curation
    review_status   TEXT DEFAULT 'pending',
    is_archived     INTEGER NOT NULL DEFAULT 0,
    archived_at     TEXT
);

CREATE INDEX IF NOT EXISTS ix_font_samples_slug ON font_samples(slug);
CREATE INDEX IF NOT EXISTS ix_font_samples_review_status ON font_samples(review_status);
CREATE INDEX IF NOT EXISTS ix_font_samples_is_archived ON font_samples(is_archived);

-- Glyphs
CREATE TABLE IF NOT EXISTS glyphs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id   INTEGER NOT NULL REFERENCES font_samples(id) ON DELETE CASCADE,
    filename    TEXT NOT NULL,
    bbox_x      INTEGER NOT NULL,
    bbox_y      INTEGER NOT NULL,
    bbox_w      INTEGER NOT NULL,
    bbox_h      INTEGER NOT NULL,
    label       TEXT,
    advance_width  INTEGER,
    left_bearing   INTEGER,
    verified    INTEGER NOT NULL DEFAULT 0,
    synthesized INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS ix_glyphs_sample_id ON glyphs(sample_id);

-- Font Variants
CREATE TABLE IF NOT EXISTS font_variants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id       INTEGER NOT NULL REFERENCES font_samples(id) ON DELETE CASCADE,
    variant_name    TEXT NOT NULL,
    weight          TEXT,
    width           TEXT,
    slope           TEXT,
    optical_size    TEXT,
    lifecycle_state TEXT NOT NULL DEFAULT 'draft',
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE(sample_id, variant_name)
);

CREATE INDEX IF NOT EXISTS ix_font_variants_sample_id ON font_variants(sample_id);

-- Font Aliases
CREATE TABLE IF NOT EXISTS font_aliases (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id   INTEGER NOT NULL REFERENCES font_samples(id) ON DELETE CASCADE,
    alias       TEXT NOT NULL,
    locale      TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE(sample_id, alias)
);

CREATE INDEX IF NOT EXISTS ix_font_aliases_sample_id ON font_aliases(sample_id);
CREATE INDEX IF NOT EXISTS ix_font_aliases_alias ON font_aliases(alias);

-- Font Files
CREATE TABLE IF NOT EXISTS font_files (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id   INTEGER NOT NULL REFERENCES font_samples(id) ON DELETE CASCADE,
    variant_id  INTEGER REFERENCES font_variants(id) ON DELETE SET NULL,
    filename    TEXT NOT NULL,
    file_format TEXT NOT NULL,
    file_size   INTEGER,
    sha256      TEXT,
    is_primary  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS ix_font_files_sample_id ON font_files(sample_id);

-- Preview Assets
CREATE TABLE IF NOT EXISTS preview_assets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id   INTEGER NOT NULL REFERENCES font_samples(id) ON DELETE CASCADE,
    variant_id  INTEGER REFERENCES font_variants(id) ON DELETE SET NULL,
    asset_type  TEXT NOT NULL,
    filename    TEXT NOT NULL,
    width       INTEGER,
    height      INTEGER,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS ix_preview_assets_sample_id ON preview_assets(sample_id);

-- Glyph Coverage Summary
CREATE TABLE IF NOT EXISTS glyph_coverage_summaries (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id           INTEGER NOT NULL UNIQUE REFERENCES font_samples(id) ON DELETE CASCADE,
    total_glyphs        INTEGER NOT NULL DEFAULT 0,
    verified_glyphs     INTEGER NOT NULL DEFAULT 0,
    latin_basic_count   INTEGER NOT NULL DEFAULT 0,
    latin_extended_count INTEGER NOT NULL DEFAULT 0,
    digits_count        INTEGER NOT NULL DEFAULT 0,
    punctuation_count   INTEGER NOT NULL DEFAULT 0,
    coverage_percent    REAL NOT NULL DEFAULT 0.0,
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- Taxonomy Dimensions
CREATE TABLE IF NOT EXISTS taxonomy_dimensions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    label       TEXT NOT NULL,
    cardinality TEXT NOT NULL DEFAULT 'single',
    filterable  INTEGER NOT NULL DEFAULT 1,
    sortable    INTEGER NOT NULL DEFAULT 0,
    required    INTEGER NOT NULL DEFAULT 0
);

-- Taxonomy Terms
CREATE TABLE IF NOT EXISTS taxonomy_terms (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dimension_id    INTEGER NOT NULL REFERENCES taxonomy_dimensions(id) ON DELETE CASCADE,
    value           TEXT NOT NULL,
    parent_id       INTEGER REFERENCES taxonomy_terms(id),
    sort_order      INTEGER NOT NULL DEFAULT 0,
    synonyms        TEXT NOT NULL DEFAULT '[]',
    UNIQUE(dimension_id, value)
);

CREATE INDEX IF NOT EXISTS ix_taxonomy_terms_dimension_id ON taxonomy_terms(dimension_id);
CREATE INDEX IF NOT EXISTS ix_taxonomy_terms_value ON taxonomy_terms(value);

-- Font Sample ↔ Taxonomy Term junction
CREATE TABLE IF NOT EXISTS font_sample_taxonomy (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id   INTEGER NOT NULL REFERENCES font_samples(id) ON DELETE CASCADE,
    term_id     INTEGER NOT NULL REFERENCES taxonomy_terms(id) ON DELETE CASCADE,
    assigned_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE(sample_id, term_id)
);

CREATE INDEX IF NOT EXISTS ix_sample_taxonomy_sample ON font_sample_taxonomy(sample_id);
CREATE INDEX IF NOT EXISTS ix_sample_taxonomy_term ON font_sample_taxonomy(term_id);

-- Source Artifacts
CREATE TABLE IF NOT EXISTS source_artifacts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id           INTEGER NOT NULL REFERENCES font_samples(id) ON DELETE CASCADE,
    artifact_type       TEXT NOT NULL,
    title               TEXT,
    publisher           TEXT,
    publication_date    TEXT,
    repository          TEXT,
    identifier          TEXT,
    scan_filename       TEXT,
    scan_resolution_dpi INTEGER,
    rights_statement    TEXT,
    rights_uri          TEXT,
    notes               TEXT,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS ix_source_artifacts_sample_id ON source_artifacts(sample_id);

-- Provenance Records
CREATE TABLE IF NOT EXISTS provenance_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id       INTEGER NOT NULL REFERENCES font_samples(id) ON DELETE CASCADE,
    artifact_id     INTEGER REFERENCES source_artifacts(id) ON DELETE SET NULL,
    event_type      TEXT NOT NULL,
    actor           TEXT,
    outcome         TEXT,
    confidence      REAL,
    completeness    REAL,
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS ix_provenance_sample_id ON provenance_records(sample_id);
CREATE INDEX IF NOT EXISTS ix_provenance_sample_event ON provenance_records(sample_id, event_type);

-- Curation Audit Log (append-only)
CREATE TABLE IF NOT EXISTS curation_audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id   INTEGER REFERENCES font_samples(id) ON DELETE SET NULL,
    actor       TEXT,
    action      TEXT NOT NULL,
    entity_type TEXT,
    entity_id   INTEGER,
    field_name  TEXT,
    old_value   TEXT,
    new_value   TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS ix_audit_log_sample_id ON curation_audit_log(sample_id);

-- API Keys
CREATE TABLE IF NOT EXISTS api_keys (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key         TEXT NOT NULL UNIQUE,
    owner       TEXT NOT NULL,
    scope       TEXT NOT NULL DEFAULT 'read',
    is_active   INTEGER NOT NULL DEFAULT 1,
    rate_limit  INTEGER NOT NULL DEFAULT 1000,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS ix_api_keys_key ON api_keys(key);
CREATE INDEX IF NOT EXISTS ix_api_keys_owner ON api_keys(owner);

-- Jobs
CREATE TABLE IF NOT EXISTS jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    kind            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'queued',
    sample_id       INTEGER REFERENCES font_samples(id) ON DELETE SET NULL,
    input_params    TEXT,
    engine_version  TEXT NOT NULL,
    error_detail    TEXT,
    started_at      TEXT,
    finished_at     TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS ix_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS ix_jobs_sample_id ON jobs(sample_id);

-- Font Builds
CREATE TABLE IF NOT EXISTS font_builds (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id           INTEGER NOT NULL REFERENCES font_samples(id) ON DELETE CASCADE,
    job_id              INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
    format              TEXT NOT NULL,
    filename            TEXT NOT NULL,
    file_size           INTEGER,
    sha256              TEXT,
    source_package_id   INTEGER,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS ix_font_builds_sample_id ON font_builds(sample_id);

-- Search Index (denormalized for fast faceting)
CREATE TABLE IF NOT EXISTS font_search_index (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id       INTEGER NOT NULL UNIQUE REFERENCES font_samples(id) ON DELETE CASCADE,
    font_name       TEXT,
    font_category   TEXT,
    style           TEXT,
    genre           TEXT,
    era             TEXT,
    origin_context  TEXT,
    restoration_status TEXT,
    rights_status   TEXT,
    review_status   TEXT,
    confidence      REAL,
    completeness    REAL,
    glyph_count     INTEGER NOT NULL DEFAULT 0,
    tags            TEXT NOT NULL DEFAULT '[]',
    moods           TEXT NOT NULL DEFAULT '[]',
    use_cases       TEXT NOT NULL DEFAULT '[]',
    visual_traits   TEXT NOT NULL DEFAULT '[]',
    construction_traits TEXT NOT NULL DEFAULT '[]',
    search_text     TEXT,
    feature_vector  TEXT NOT NULL DEFAULT '{}',
    indexed_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS ix_search_font_name ON font_search_index(font_name);
CREATE INDEX IF NOT EXISTS ix_search_font_category ON font_search_index(font_category);
CREATE INDEX IF NOT EXISTS ix_search_style ON font_search_index(style);
CREATE INDEX IF NOT EXISTS ix_search_genre ON font_search_index(genre);
CREATE INDEX IF NOT EXISTS ix_search_era ON font_search_index(era);
CREATE INDEX IF NOT EXISTS ix_search_review_status ON font_search_index(review_status);
"#;
