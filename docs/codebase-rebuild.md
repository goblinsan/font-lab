# Codebase Rebuild Plan

This document describes how to rebuild **font-lab** from the current Python
codebase into the target TypeScript and Rust architecture.

The project is still young. That changes the migration strategy:

- keep the current code as a behavior reference
- do not preserve the current internal structure
- rebuild cleanly while behavior is still small enough to verify

---

## Rebuild Strategy

This should be treated as a **greenfield rebuild with a reference oracle**.

The existing Python app is useful for:

- route and workflow discovery
- fixture generation
- expected behavior in tests
- understanding edge cases already encoded in logic

It should not dictate the structure of the new codebase.

---

## What Carries Forward

- product behavior that is still desirable
- real sample fixtures and expected outputs
- useful request and response shapes
- migration notes captured in docs
- test intent encoded under [`tests/`](../tests)

---

## What Does Not Carry Forward

- the current module layout
- duplicated catalog surfaces
- database JSON-as-text shortcuts
- filesystem assumptions baked into route handlers
- synchronous processing inside the request path
- mixed responsibilities in one module

---

## Current Code Areas To Mine

Use these files as source material during the rebuild:

- [`app/main.py`](../app/main.py)
- [`app/models.py`](../app/models.py)
- [`app/repository.py`](../app/repository.py)
- [`app/routes/images.py`](../app/routes/images.py)
- [`app/routes/glyphs.py`](../app/routes/glyphs.py)
- [`app/routes/reconstruction.py`](../app/routes/reconstruction.py)
- [`app/routes/catalog.py`](../app/routes/catalog.py)
- [`app/routes/v1/catalog.py`](../app/routes/v1/catalog.py)
- [`app/routes/v1/keys.py`](../app/routes/v1/keys.py)
- [`app/segmentation.py`](../app/segmentation.py)
- [`app/vectorize.py`](../app/vectorize.py)
- [`app/reconstruction.py`](../app/reconstruction.py)
- [`app/font_export.py`](../app/font_export.py)
- [`tests/`](../tests)

---

## Milestones

## Milestone 0: Freeze Scope and Capture Behavior

Goal:

- define what the new system must do before writing new code

Tasks:

- list every current route and decide whether it survives unchanged, changes,
  or is dropped
- collect representative sample images and expected outputs
- extract golden fixtures from the current tests
- define the first stable v1 API surface for the rebuilt backend

Deliverables:

- fixture corpus under `fixtures/`
- route inventory
- kept vs dropped feature list

Exit criteria:

- the team can explain the v1 feature set without referring to the Python app

---

## Milestone 1: Create the New Repository Structure

Goal:

- create the new TypeScript and Rust workspace layout

Tasks:

- add Cargo workspace for Rust crates
- add `apps/web` for the frontend
- add CI for formatting, linting, tests, and fixture validation
- set up consistent environment configuration for local development

Deliverables:

- empty crate layout matching the target architecture
- working frontend shell
- working Rust API and worker entrypoints

Exit criteria:

- the repo builds in CI with placeholder modules in place

---

## Milestone 2: Rebuild the Data Model in Rust

Goal:

- move the data model and persistence layer into Rust with a cleaner schema

Tasks:

- port the useful parts of [`app/models.py`](../app/models.py) into `domain`
- define SQLx migrations
- split metadata, binary assets, jobs, and build artifacts into clear tables
- keep SQLite first
- model state transitions explicitly instead of relying on loose nullable fields

Deliverables:

- migrations
- domain entities and repository interfaces
- projection queries for catalog and glyph views

Exit criteria:

- sample, glyph, build, and job records can be created and queried in tests

---

## Milestone 3: Rebuild the HTTP API in Rust

Goal:

- replace the current Python CRUD and query endpoints with Rust endpoints

Tasks:

- port sample upload, list, get, update, and delete behavior
- port glyph listing and mutation behavior
- port catalog and search behavior
- port API key management
- remove duplicate route logic and expose a single versioned API

Deliverables:

- `/api/v1/samples`
- `/api/v1/glyphs`
- `/api/v1/catalog`
- `/api/v1/keys`

Exit criteria:

- the frontend can use the Rust API for metadata-only workflows

---

## Milestone 4: Port the Existing Processing Engine Exactly

Goal:

- preserve current behavior before improving algorithms

Tasks:

- port the segmentation behavior from [`app/segmentation.py`](../app/segmentation.py)
- port vector output behavior from [`app/vectorize.py`](../app/vectorize.py)
- port reconstruction behavior from [`app/reconstruction.py`](../app/reconstruction.py)
- port export behavior from [`app/font_export.py`](../app/font_export.py)
- keep outputs close enough to current fixtures that regressions are obvious

Deliverables:

- Rust segmentation jobs
- Rust export jobs
- Rust processing tests against golden fixtures

Exit criteria:

- fixture comparisons show functional parity for the current supported flows

Why this milestone matters:

- it separates "language migration" from "algorithm redesign"
- it avoids accidental product changes during the rewrite

---

## Milestone 5: Replace the Frontend

Goal:

- replace the static frontend with a typed product UI

Tasks:

- replace [`app/static/index.html`](../app/static/index.html) with React pages
- add typed API client generation
- build catalog browsing
- build sample detail and glyph review
- build export request and build history views

Deliverables:

- usable editor workflow in TypeScript
- typed API client package

Exit criteria:

- the Python frontend is no longer needed for day-to-day product use

---

## Milestone 6: Introduce Durable Font Source Packages

Goal:

- move from ad hoc export logic to a more durable source model

Tasks:

- generate UFO packages from approved glyph data
- persist source package versions in blob storage
- track which source package produced each export artifact
- keep compatibility mode for the simpler current export path until the UFO
  path is proven

Deliverables:

- `font_source` crate
- versioned source bundles
- artifact lineage from source to export

Exit criteria:

- every export can be traced to a concrete reviewed source package

---

## Milestone 7: Add OCR and Validation as Background Capabilities

Goal:

- improve the engine without turning it into an opaque black box

Tasks:

- add OCR suggestions behind an adapter interface
- keep OCR asynchronous and reviewable
- add parser smoke tests for exported fonts
- add render and shaping smoke tests in the validation path

Deliverables:

- OCR suggestion jobs
- export validation jobs
- validation reports attached to builds

Exit criteria:

- OCR is helpful but never authoritative
- builds fail loudly when outputs are malformed

---

## Milestone 8: Cut Over and Remove Python

Goal:

- retire the Python code once the new stack owns the product

Tasks:

- dual-run fixture comparisons between Python and Rust where useful
- point the frontend entirely at the Rust API
- archive or remove Python-only application code
- keep fixture-based regression tests for long-term protection

Deliverables:

- Rust as the only runtime backend
- TypeScript as the only product frontend

Exit criteria:

- the Python service is no longer required in development or production

---

## Recommended Build Order

If execution needs a strict order, use this:

1. Milestone 0: scope and fixtures
2. Milestone 1: workspace skeleton
3. Milestone 2: schema and persistence
4. Milestone 3: Rust metadata API
5. Milestone 4: processing engine parity
6. Milestone 5: TypeScript frontend
7. Milestone 6: durable source packages
8. Milestone 7: OCR and validation
9. Milestone 8: cutover

This order keeps the highest-risk work visible early while preventing the
frontend from blocking backend architecture decisions.

---

## Workstreams

These can run in parallel after the first two milestones:

- backend domain and persistence
- processing engine parity
- frontend shell and layout
- fixture generation and regression harness

Keep one rule in place:

- no workstream is allowed to invent its own domain model outside `domain`

---

## Quality Gates

Every milestone should maintain these quality gates:

- all Rust code formatted and linted
- all frontend code typed and linted
- fixture-based tests stay green
- binary outputs are validated, not just generated
- API contracts are documented and testable

---

## What To Avoid During the Rebuild

- do not rewrite the product and the algorithms in the same step
- do not introduce distributed systems concerns on day one
- do not couple OCR directly to approval state
- do not store long-term truth only in exported font binaries
- do not preserve awkward Python-era route duplication for compatibility alone

---

## Suggested First Tickets

The first ten tickets should be:

1. Create fixture corpus from current tests and sample images.
2. Write route inventory and decide keep/change/drop.
3. Create Cargo workspace and crate skeletons.
4. Create `apps/web` Vite + React + TypeScript shell.
5. Add SQLx migrations for `samples`, `glyphs`, `jobs`, and `builds`.
6. Implement Rust upload and sample list endpoints.
7. Implement Rust glyph list and patch endpoints.
8. Port segmentation algorithm with fixture assertions.
9. Build initial catalog and glyph review frontend.
10. Implement export job skeleton with build status tracking.

---

## Definition of Done

The rebuild is done when:

- all product-facing UI runs in TypeScript
- all server-side behavior runs in Rust
- segmentation, export, and review workflows are covered by fixtures
- exported builds are versioned and validated
- the Python application is no longer needed as a runtime dependency

---

## Summary

The rebuild plan is intentionally conservative:

- preserve useful behavior
- rebuild structure cleanly
- keep infrastructure small
- make the font engine testable
- only add OCR and more advanced processing after parity is achieved

That is the lowest-debt path from the current Python codebase to a durable
TypeScript and Rust system.
