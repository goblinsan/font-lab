# Database Architecture & ERD

This document describes the full relational schema for **font-lab**, the
entity–relationship diagram (ERD), indexing strategy, and how each table maps
to taxonomy, API responses, and reconstruction workflows.

---

## Contents

1. [Overview](#overview)
2. [Entity–Relationship Diagram](#entity-relationship-diagram)
3. [Table Descriptions](#table-descriptions)
   - [font\_samples](#font_samples)
   - [font\_variants](#font_variants)
   - [font\_aliases](#font_aliases)
   - [font\_files](#font_files)
   - [glyphs](#glyphs)
   - [glyph\_coverage\_summaries](#glyph_coverage_summaries)
   - [preview\_assets](#preview_assets)
   - [taxonomy\_dimensions](#taxonomy_dimensions)
   - [taxonomy\_terms](#taxonomy_terms)
   - [font\_sample\_taxonomy](#font_sample_taxonomy)
   - [source\_artifacts](#source_artifacts)
   - [provenance\_records](#provenance_records)
   - [font\_search\_index](#font_search_index)
   - [api\_keys](#api_keys)
4. [Indexing Strategy](#indexing-strategy)
5. [Taxonomy Mapping](#taxonomy-mapping)
6. [API Response Mapping](#api-response-mapping)
7. [Reconstruction Workflow Mapping](#reconstruction-workflow-mapping)
8. [Migration Strategy](#migration-strategy)
9. [Seed Data](#seed-data)

---

## Overview

Font-lab persists all data in a **SQLite** database by default (configurable
via the `DATABASE_URL` environment variable to any SQLAlchemy-compatible
engine, e.g. PostgreSQL for production).

The schema is grouped into four functional areas:

| Area | Tables |
|------|--------|
| **Font catalog** | `font_samples`, `font_variants`, `font_aliases`, `font_files` |
| **Glyph data** | `glyphs`, `glyph_coverage_summaries`, `preview_assets` |
| **Taxonomy** | `taxonomy_dimensions`, `taxonomy_terms`, `font_sample_taxonomy` |
| **Provenance** | `source_artifacts`, `provenance_records` |
| **Search** | `font_search_index` |
| **Auth** | `api_keys` |

---

## Entity–Relationship Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                             font_samples (root)                            │
│  id · filename · original_filename · font_name · font_category · style    │
│  genre · theme · era · provenance · confidence · notes · source            │
│  restoration_notes · tags · file_size · content_type · uploaded_at         │
│  origin_context · source_type · restoration_status · rights_status         │
│  rights_notes · completeness · moods · use_cases                           │
│  construction_traits · visual_traits                                        │
└───┬────────┬────────┬────────┬──────────┬──────────┬───────────────────────┘
    │        │        │        │          │          │
    │1:N     │1:N     │1:N     │1:1       │1:N       │1:N
    ▼        ▼        ▼        ▼          ▼          ▼
font_      font_    font_   glyph_     source_   provenance_
variants   aliases  files  coverage_  artifacts  records
           │                summaries
           │1:N
           ▼
        preview_assets
        (via variant_id or sample_id)

    │1:N
    ▼
  glyphs
    │
    │aggregated into
    ▼
glyph_coverage_summaries


  font_samples ──── font_sample_taxonomy ──── taxonomy_terms
                           (N:M)                    │N:1
                                             taxonomy_dimensions


  font_samples ─── font_search_index (1:1 denormalized projection)
```

---

## Table Descriptions

### font_samples

The **root aggregate** for any font that has been uploaded or catalogued.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment identifier |
| filename | VARCHAR(255) UNIQUE | Internal storage filename (UUID-based) |
| original_filename | VARCHAR(255) | Original upload filename |
| font_name | VARCHAR(255) | Human-readable font name |
| font_category | VARCHAR(100) | Primary intended use category |
| style | VARCHAR(100) | Primary style family (Serif, Sans-Serif, …) |
| genre | VARCHAR(100) | Secondary genre within style |
| theme | VARCHAR(100) | Aesthetic theme |
| era | VARCHAR(100) | Historical period |
| provenance | TEXT | Free-text provenance description |
| confidence | FLOAT | Reconstruction confidence [0, 1] |
| notes | TEXT | Curator notes |
| source | TEXT | Source reference |
| restoration_notes | TEXT | Notes on the restoration process |
| tags | TEXT (JSON) | Free-form tag list |
| file_size | INTEGER | File size in bytes |
| content_type | VARCHAR(100) | MIME type of the uploaded image |
| uploaded_at | DATETIME(tz) | Upload timestamp |
| origin_context | VARCHAR(100) | Geographic/cultural provenance |
| source_type | VARCHAR(100) | Physical or digital artifact type |
| restoration_status | VARCHAR(100) | Digitisation workflow stage |
| rights_status | VARCHAR(100) | Licensing / rights classification |
| rights_notes | TEXT | Rights details |
| completeness | FLOAT | Estimated glyph set completeness [0, 1] |
| moods | TEXT (JSON) | Expressive mood list |
| use_cases | TEXT (JSON) | Intended use-case list |
| construction_traits | TEXT (JSON) | Structural feature list |
| visual_traits | TEXT (JSON) | Visual feature list |

---

### font_variants

Named typographic variants (weights, widths, optical sizes) of a
`font_sample`.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| sample_id | INTEGER FK → font_samples | Cascade delete |
| variant_name | VARCHAR(255) | e.g. "Bold Italic", "Caption" |
| weight | VARCHAR(100) | Typographic weight string |
| width | VARCHAR(100) | Typographic width string |
| slope | VARCHAR(100) | Italic / oblique indicator |
| optical_size | VARCHAR(100) | Optical size range label |
| lifecycle_state | VARCHAR(50) | draft / ready / published / archived |
| created_at | DATETIME(tz) | |
| updated_at | DATETIME(tz) | Auto-updated on modification |

**Unique constraint**: `(sample_id, variant_name)`.

---

### font_aliases

Alternative or historical names for a `font_sample`.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| sample_id | INTEGER FK → font_samples | Cascade delete |
| alias | VARCHAR(255) | Alternative name |
| locale | VARCHAR(20) | Optional BCP-47 locale code |
| created_at | DATETIME(tz) | |

**Unique constraint**: `(sample_id, alias)`.

---

### font_files

Reconstructed font binary files (TTF, OTF, WOFF2, etc.) linked to a
`font_sample` or `font_variant`.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| sample_id | INTEGER FK → font_samples | Cascade delete |
| variant_id | INTEGER FK → font_variants | Nullable (SET NULL on delete) |
| filename | VARCHAR(255) | Storage path |
| file_format | VARCHAR(20) | ttf / otf / woff / woff2 / ufo |
| file_size | INTEGER | Bytes |
| sha256 | VARCHAR(64) | Integrity hash |
| is_primary | BOOLEAN | Primary download file flag |
| created_at | DATETIME(tz) | |

---

### glyphs

Individual character crops segmented from a `font_sample` image.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| sample_id | INTEGER FK → font_samples | Cascade delete |
| filename | VARCHAR(255) | Cropped glyph image path |
| bbox_x/y/w/h | INTEGER | Bounding box in source image |
| label | VARCHAR(10) | Unicode character label |
| advance_width | INTEGER | Typographic advance width |
| left_bearing | INTEGER | Left side bearing |
| verified | BOOLEAN | Human-verified label flag |
| synthesized | BOOLEAN | Computationally synthesized flag |
| created_at | DATETIME(tz) | |

---

### glyph_coverage_summaries

Aggregated per-`font_sample` coverage statistics, one row per sample.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| sample_id | INTEGER FK → font_samples UNIQUE | Cascade delete |
| total_glyphs | INTEGER | Total glyph crops |
| verified_glyphs | INTEGER | Human-verified count |
| latin_basic_count | INTEGER | Basic Latin characters |
| latin_extended_count | INTEGER | Extended Latin characters |
| digits_count | INTEGER | Digit characters |
| punctuation_count | INTEGER | Punctuation characters |
| coverage_percent | FLOAT | Estimated % of printable ASCII covered |
| updated_at | DATETIME(tz) | Auto-updated |

---

### preview_assets

Rendered specimen or preview images for a `font_sample` or `font_variant`.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| sample_id | INTEGER FK → font_samples | Cascade delete |
| variant_id | INTEGER FK → font_variants | Nullable |
| asset_type | VARCHAR(50) | waterfall / grid / specimen / thumbnail |
| filename | VARCHAR(255) | Storage path |
| width | INTEGER | Pixel width |
| height | INTEGER | Pixel height |
| created_at | DATETIME(tz) | |

---

### taxonomy_dimensions

Controlled-vocabulary dimensions (e.g. "style", "genre", "moods").

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| name | VARCHAR(100) UNIQUE | Machine key (e.g. `style`) |
| label | VARCHAR(200) | Human label (e.g. `Style Family`) |
| cardinality | VARCHAR(10) | `single` or `multi` |
| filterable | BOOLEAN | Exposed as a filter facet |
| sortable | BOOLEAN | Usable as a sort key |
| required | BOOLEAN | Mandatory field flag |

---

### taxonomy_terms

Individual controlled-vocabulary values within a `taxonomy_dimension`.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| dimension_id | INTEGER FK → taxonomy_dimensions | Cascade delete |
| value | VARCHAR(255) | Term value (e.g. `Serif`) |
| parent_id | INTEGER FK → taxonomy_terms | Optional parent for hierarchy |
| sort_order | INTEGER | Display order within dimension |
| synonyms | TEXT (JSON) | Accepted synonym strings |

**Unique constraint**: `(dimension_id, value)`.

---

### font_sample_taxonomy

Many-to-many junction linking `font_samples` to `taxonomy_terms`.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| sample_id | INTEGER FK → font_samples | Cascade delete |
| term_id | INTEGER FK → taxonomy_terms | Cascade delete |
| assigned_at | DATETIME(tz) | When the term was assigned |

**Unique constraint**: `(sample_id, term_id)`.

This table is the normalized alternative to the JSON multi-value columns on
`font_samples`.  It enables efficient `GROUP BY` facet-count queries without
loading all records into memory.

---

### source_artifacts

Physical or digital source items from which a font was derived.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| sample_id | INTEGER FK → font_samples | Cascade delete |
| artifact_type | VARCHAR(100) | e.g. "Printed Specimen", "Book" |
| title | VARCHAR(500) | Source title |
| publisher | VARCHAR(255) | Publisher / foundry |
| publication_date | VARCHAR(50) | Free-form date string |
| repository | VARCHAR(500) | Holding institution or URL |
| identifier | VARCHAR(255) | ISBN, call number, URL, etc. |
| scan_filename | VARCHAR(255) | Path to the raw scan file |
| scan_resolution_dpi | INTEGER | Scan resolution |
| rights_statement | TEXT | Full rights statement |
| rights_uri | VARCHAR(500) | URI to rights document |
| notes | TEXT | Additional notes |
| created_at | DATETIME(tz) | |

---

### provenance_records

Timestamped event log of all restoration and review steps for a
`font_sample`.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| sample_id | INTEGER FK → font_samples | Cascade delete |
| artifact_id | INTEGER FK → source_artifacts | Optional, SET NULL |
| event_type | VARCHAR(100) | upload / segmentation / outlining / kerning / rights_review / … |
| actor | VARCHAR(255) | User or service identifier |
| outcome | VARCHAR(100) | success / failure / skipped |
| confidence | FLOAT | Reconstruction confidence at this step |
| completeness | FLOAT | Estimated completeness at this step |
| notes | TEXT | Step notes |
| created_at | DATETIME(tz) | |

**Composite index**: `(sample_id, event_type)`.

---

### font_search_index

Denormalized one-row-per-font projection used by search and ranking queries.
Updated asynchronously after every metadata write.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| sample_id | INTEGER FK → font_samples UNIQUE | Cascade delete |
| font_name | VARCHAR(255) | Indexed copy |
| font_category | VARCHAR(100) | Indexed copy |
| style | VARCHAR(100) | Indexed copy |
| genre | VARCHAR(100) | Indexed copy |
| era | VARCHAR(100) | Indexed copy |
| origin_context | VARCHAR(100) | Indexed copy |
| restoration_status | VARCHAR(100) | Indexed copy |
| rights_status | VARCHAR(100) | Indexed copy |
| confidence | FLOAT | Indexed copy |
| completeness | FLOAT | Indexed copy |
| glyph_count | INTEGER | Denormalized from `glyphs` count |
| tags | TEXT (JSON) | Denormalized copy |
| moods | TEXT (JSON) | Denormalized copy |
| use_cases | TEXT (JSON) | Denormalized copy |
| visual_traits | TEXT (JSON) | Denormalized copy |
| construction_traits | TEXT (JSON) | Denormalized copy |
| search_text | TEXT | Concatenated full-text blob |
| feature_vector | TEXT (JSON) | Similarity feature object |
| indexed_at | DATETIME(tz) | Last indexing timestamp |

Individual scalar columns each have a B-tree index to accelerate
`WHERE style = ?` / `WHERE era = ?`-style filter queries.

---

### api_keys

Developer API keys controlling access to the versioned `/api/v1/` endpoints.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| key | VARCHAR(64) UNIQUE | Cryptographically random token |
| owner | VARCHAR(255) | Owner identifier |
| scope | VARCHAR(100) | read / write / admin |
| is_active | BOOLEAN | Revocation flag |
| rate_limit | INTEGER | Requests per period |
| created_at | DATETIME(tz) | |

---

## Indexing Strategy

| Table | Index | Purpose |
|-------|-------|---------|
| `font_samples` | `id` (PK) | Lookups by ID |
| `font_samples` | `filename` (UNIQUE) | Deduplication on upload |
| `glyphs` | `sample_id` | Join from sample to glyphs |
| `font_variants` | `sample_id` | Join from sample to variants |
| `font_aliases` | `sample_id`, `alias` | Alias lookups |
| `taxonomy_terms` | `dimension_id`, `value` | Term resolution |
| `font_sample_taxonomy` | `sample_id`, `term_id`, composite | Facet joins |
| `provenance_records` | `(sample_id, event_type)` | Workflow history queries |
| `font_search_index` | `sample_id` (UNIQUE) | 1:1 lookup |
| `font_search_index` | `style`, `genre`, `era`, `origin_context`, … | Per-facet filter scans |

On **PostgreSQL**, the `search_text` column should additionally be indexed
with a GIN tsvector index for full-text search:

```sql
CREATE INDEX ix_font_search_text ON font_search_index USING GIN (to_tsvector('english', search_text));
```

---

## Taxonomy Mapping

The taxonomy module (`app/taxonomy.py`) defines Python-level controlled
vocabularies.  These are **mirrored** into the database as
`taxonomy_dimensions` + `taxonomy_terms` rows via the seed script
(`scripts/seed_taxonomy.py`).

| Python constant | `taxonomy_dimensions.name` | Cardinality |
|-----------------|---------------------------|-------------|
| `STYLES` | `style` | single |
| `GENRES` | `genre` | single |
| `THEMES` | `themes` | multi |
| `MOODS` | `moods` | multi |
| `CATEGORIES` | `font_category` | single |
| `USE_CASES` | `use_cases` | multi |
| `ERAS` | `era` | single |
| `ORIGIN_CONTEXTS` | `origin_context` | single |
| `CONSTRUCTION_TRAITS` | `construction_traits` | multi |
| `VISUAL_TRAITS` | `visual_traits` | multi |
| `RESTORATION_STATUSES` | `restoration_status` | single |
| `SOURCE_TYPES` | `source_type` | single |
| `RIGHTS_STATUSES` | `rights_status` | single |

`SYNONYMS` are stored per-term in `taxonomy_terms.synonyms` (JSON list).
`HIERARCHY` (style → genre parent/child) is represented via
`taxonomy_terms.parent_id` self-referencing FK.

---

## API Response Mapping

| API endpoint | Primary table(s) | Notes |
|---|---|---|
| `GET /api/samples/` | `font_samples` | Flat list with JSON multi-value columns |
| `GET /api/v1/fonts` | `font_samples`, `glyphs` (count) | Paginated, sortable |
| `GET /api/v1/fonts/search` | `font_samples` | Full-text LIKE + facet filters |
| `GET /api/v1/fonts/{id}` | `font_samples`, `glyphs` (count) | Single record |
| `GET /api/v1/fonts/{id}/similar` | `font_samples` | In-memory Jaccard scoring |
| `GET /api/v1/fonts/{id}/preview` | `font_samples`, `glyphs` | Embeddable config |
| `GET /api/taxonomy/` | Python constants (`taxonomy.py`) | Not DB-backed at runtime |

The `font_search_index` table is designed to accelerate the `search` and
`list` endpoints in future by replacing full `font_samples` table scans.

---

## Reconstruction Workflow Mapping

The reconstruction pipeline produces the following records:

1. **Upload** → `font_samples` row created; `provenance_records` event
   `event_type = "upload"` appended.
2. **Segmentation** (`/api/samples/{id}/segment`) → `glyphs` rows inserted;
   `glyph_coverage_summaries` upserted; `provenance_records` event
   `event_type = "segmentation"`.
3. **Vectorisation** → `font_files` row added with `file_format = "svg"`;
   provenance event `event_type = "vectorisation"`.
4. **Reconstruction / export** → `font_files` rows added for TTF/OTF/WOFF2;
   `font_variants` row created if named; provenance event
   `event_type = "export"`.
5. **Rights review** → `source_artifacts` row linked;
   `font_samples.rights_status` updated; provenance event
   `event_type = "rights_review"`.
6. **Publication** → `font_samples.restoration_status = "Published"`;
   `font_variants.lifecycle_state = "published"`.

---

## Migration Strategy

Database schema changes are managed with **Alembic**.

```bash
# Apply all pending migrations
alembic upgrade head

# Generate a new migration from model changes
alembic revision --autogenerate -m "description"

# Downgrade one step
alembic downgrade -1
```

The `DATABASE_URL` environment variable is read by `alembic/env.py` and
overrides the default `sqlite:///./font_lab.db` in `alembic.ini`.

For **testing**, an in-memory SQLite database is used and all tables are
created directly with `Base.metadata.create_all()` (no Alembic needed).

---

## Seed Data

Taxonomy dimensions and terms can be seeded (or re-seeded after schema
changes) with:

```bash
DATABASE_URL=sqlite:///./font_lab.db python scripts/seed_taxonomy.py
```

The script is **idempotent**: it calls `upsert_dimension` and `upsert_term`
rather than plain inserts, so re-running will update existing rows rather
than raise duplicate-key errors.
