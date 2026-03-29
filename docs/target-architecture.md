# Target Architecture

This document defines the target architecture for rebuilding **font-lab** as a
TypeScript frontend with a Rust backend.

The goal is not "rewrite for rewrite's sake". The goal is a stable,
maintainable font processing system with clear boundaries between:

- product UI
- API and application orchestration
- raster analysis and OCR
- font engineering and export

---

## Goals

- Use **TypeScript** for the product-facing frontend.
- Use **Rust** for the backend and font processing engine.
- Avoid service sprawl and premature infrastructure.
- Preserve the useful behavior in the current Python codebase without carrying
  forward avoidable design debt.
- Make font processing outputs reproducible, testable, and versioned.

---

## Non-Goals

- No microservices on day one.
- No OpenCV dependency on day one.
- No OCR in the synchronous request path.
- No OTF or TTF files as the canonical source of truth.
- No duplication between unversioned and versioned APIs in the new system.

---

## System Shape

Build the new system as a **modular monorepo**:

```text
font-lab/
  apps/
    web/                  # React + TypeScript + Vite frontend
  crates/
    api/                  # axum HTTP server
    application/          # use-cases, orchestration, transactions
    domain/               # entities, value objects, policies, errors
    db/                   # SQLx queries and migrations
    blob_store/           # local filesystem now, S3-compatible later
    image_core/           # decoding, preprocessing, thresholding, metrics
    segmentation/         # glyph segmentation algorithms
    ocr/                  # OCR traits and adapters
    font_source/          # canonical UFO package generation
    font_engine/          # font parsing, writing, validation
    worker/               # async jobs: segment, OCR, export, validation
    cli/                  # import, export, debug, fixture tooling
  packages/
    api-client/           # generated TypeScript client from OpenAPI
  fixtures/
    samples/              # golden raster inputs
    fonts/                # golden export artifacts
```

This is intentionally a **modular monolith**. There should be one Rust API
binary and one Rust worker binary. If the system needs to split later, the
crate boundaries will make that possible without rewriting business logic.

---

## Frontend

The frontend should be a **React + TypeScript + Vite** application.

Why:

- The current UI is a single static page in [`app/static/index.html`](../app/static/index.html).
- This product is an editor and catalog workflow, not a content-heavy SSR site.
- Vite keeps the frontend fast and simple without introducing backend coupling.

Primary frontend areas:

- catalog and search
- sample detail
- glyph review and correction
- export and build history
- admin and API key management

The frontend talks only to the Rust API. It does not communicate directly with
workers, the database, or blob storage.

---

## Backend

The backend should be a Rust HTTP API built as a modular monolith.

Recommended core stack:

- `axum` for HTTP
- `tokio` for async runtime
- `sqlx` for database access and migrations
- `serde` for serialization
- `tracing` for structured logs and spans

Design rules:

- route handlers stay thin
- use-cases live in `application`
- business rules live in `domain`
- file and object persistence lives behind `blob_store`
- processing work runs through the worker, not inside request handlers

---

## Data Storage

### Database

Use **SQLite** first. The project is new, and SQLite keeps the system simple
while still allowing a clean schema and full test coverage.

The schema should be designed so that a future move to PostgreSQL is possible
without changing the domain model.

### Blob Storage

Store binary assets outside the database:

- original uploads
- derived glyph crops
- generated SVG previews
- UFO source bundles
- exported font binaries

Start with local filesystem storage through the `blob_store` crate. Keep the
interface compatible with later S3-style storage.

---

## Canonical Source of Truth

The canonical source of truth should be:

- sample metadata in the database
- extracted glyph metadata and review state in the database
- raw and derived binary assets in blob storage
- generated **UFO packages** as the editable font source format

The canonical source of truth should **not** be exported OTF or TTF files.
Those are immutable build artifacts.

This architecture keeps the system auditable and makes rebuilds reproducible.

---

## Processing Pipeline

### Ingest

1. User uploads a sample image.
2. API stores sample metadata and raw blob.
3. API creates a segmentation job.

### Segmentation

1. Worker loads the original sample image.
2. Worker applies deterministic preprocessing and segmentation.
3. Worker stores glyph crops and bounding boxes.
4. API exposes glyphs for manual review.

### OCR

1. Worker optionally runs OCR against glyph crops or grouped regions.
2. OCR outputs are stored as suggestions with confidence scores.
3. Human review decides whether labels are accepted.

### Font Source Generation

1. Approved glyph data is transformed into a UFO package.
2. UFO package is written to blob storage and versioned.

### Export

1. Export job builds OTF or TTF artifacts from the approved source package.
2. Build artifacts are stored immutably.
3. Validation job checks parser compatibility and renderability.

---

## Domain Crate Responsibilities

### `domain`

Owns:

- `Sample`
- `Glyph`
- `GlyphSuggestion`
- `FontProject`
- `FontBuild`
- `ApiKey`
- `Job`

Also owns validation rules, state transitions, and domain errors.

### `application`

Owns use-cases such as:

- upload sample
- list catalog entries
- segment sample
- accept glyph correction
- request export
- revoke API key

### `db`

Owns:

- schema migrations
- SQL queries
- transaction boundaries
- projection queries for catalog views

### `image_core`

Owns:

- decoding uploaded images
- grayscale conversion
- thresholding
- crop extraction
- pixel metrics and simple feature extraction

### `segmentation`

Owns:

- line and glyph detection
- segmentation tuning parameters
- deterministic segmentation output

The existing logic in [`app/segmentation.py`](../app/segmentation.py) is the
starting point for behavior.

### `ocr`

Owns:

- OCR adapter traits
- Tesseract integration
- confidence normalization
- suggestion-only outputs

OCR is optional and asynchronous by design.

### `font_source`

Owns:

- building UFO packages from approved glyph data
- metadata normalization for editable font sources

### `font_engine`

Owns:

- reading and writing font data
- export orchestration
- validation helpers
- parser and shaping smoke checks

The existing logic in [`app/vectorize.py`](../app/vectorize.py),
[`app/reconstruction.py`](../app/reconstruction.py), and
[`app/font_export.py`](../app/font_export.py) is the starting point for
behavior and test cases.

### `worker`

Owns:

- job polling and execution
- retry behavior
- structured job logs
- segmentation, OCR, export, and validation tasks

---

## API Shape

Keep a versioned HTTP API and remove duplicate route surfaces.

Current duplication exists between:

- [`app/routes/catalog.py`](../app/routes/catalog.py)
- [`app/routes/v1/catalog.py`](../app/routes/v1/catalog.py)

The rebuilt system should keep one clear API surface:

- `/api/v1/samples`
- `/api/v1/glyphs`
- `/api/v1/catalog`
- `/api/v1/builds`
- `/api/v1/keys`

The frontend consumes the versioned API only.

---

## Job Model

Long-running work should use a persisted job model:

- `queued`
- `running`
- `succeeded`
- `failed`
- `canceled`

Jobs should record:

- input references
- processing parameters
- engine version
- start and finish timestamps
- error details when applicable

This makes processing reproducible and debuggable.

---

## Validation Strategy

Every export should be validated in at least three ways:

- parse and inspect with Rust font tooling
- render smoke-test with FreeType
- shape smoke-test with HarfBuzz

This is important because the long-term goal is a stable font processing
engine, not merely a working demo.

---

## Mapping From the Current Codebase

Use the current Python codebase as a behavior reference, not as the target
structure.

Current to target mapping:

- [`app/static/index.html`](../app/static/index.html) -> `apps/web`
- [`app/routes/`](../app/routes) -> `crates/api`
- [`app/models.py`](../app/models.py) -> `crates/domain` and `crates/db`
- [`app/repository.py`](../app/repository.py) -> `crates/application` and `crates/db`
- [`app/segmentation.py`](../app/segmentation.py) -> `crates/image_core` and `crates/segmentation`
- [`app/vectorize.py`](../app/vectorize.py) -> `crates/font_engine`
- [`app/reconstruction.py`](../app/reconstruction.py) -> `crates/font_engine`
- [`app/font_export.py`](../app/font_export.py) -> `crates/font_engine`

The new architecture should preserve useful behavior while removing accidental
coupling between HTTP, storage, image processing, and export logic.

---

## Recommended External Foundations

These are the main external foundations informing the target architecture:

- React: <https://react.dev/>
- Vite: <https://vite.dev/guide/>
- axum: <https://docs.rs/crate/axum/latest>
- Tokio: <https://tokio.rs/tokio/tutorial>
- SQLx: <https://docs.rs/sqlx/latest/sqlx/>
- Tesseract: <https://tesseract-ocr.github.io/tessdoc/>
- Fontations: <https://github.com/googlefonts/fontations>
- Skrifa: <https://docs.rs/skrifa/latest/skrifa/>
- read-fonts: <https://docs.rs/crate/read-fonts/latest>
- write-fonts: <https://docs.rs/crate/write-fonts/latest>
- norad: <https://docs.rs/norad>
- FreeType: <https://freetype.org/freetype2/docs/index.html>
- HarfBuzz: <https://harfbuzz.github.io/what-does-harfbuzz-do.html>

---

## Summary

The target architecture is:

- TypeScript frontend
- Rust modular monolith backend
- Rust worker for async processing
- SQLite first, blob storage abstraction from day one
- UFO as editable source of truth
- exported fonts as immutable artifacts

This keeps the product stack clear, the processing stack testable, and the
font engineering work isolated from avoidable application debt.
