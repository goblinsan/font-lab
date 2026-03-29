# font-lab

A font sample ingestion, segmentation, curation, and export system built as a
Rust + TypeScript monorepo.

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| **Rust** | 1.85+ | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh` |
| **Node.js** | 20+ | [nodejs.org](https://nodejs.org) or `brew install node` |

After installing Rust, make sure `cargo` is on your `PATH`:

```bash
source "$HOME/.cargo/env"
```

## Quick start

```bash
# 1. Build everything
cargo build

# 2. Run database migrations and seed taxonomy
cargo run --bin font-lab-cli -- migrate
cargo run --bin font-lab-cli -- seed-taxonomy

# 3. Start the API server (port 8000)
cargo run --bin font-lab-api

# 4. In a second terminal, start the worker
cargo run --bin font-lab-worker

# 5. In a third terminal, start the frontend dev server
cd apps/web
npm install   # first time only
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.
The Vite dev server proxies `/api` and `/uploads` requests to the Rust API on
port 8000.

## Running tests

```bash
cargo test
```

## Project structure

```
font-lab/
├── apps/
│   └── web/                  # React + TypeScript + Vite frontend
├── crates/
│   ├── api/                  # axum HTTP server (port 8000)
│   ├── application/          # Use-case orchestration layer
│   ├── domain/               # Entities, validation, business rules
│   ├── db/                   # SQLx migrations and repository queries
│   ├── blob_store/           # Binary asset storage (local FS)
│   ├── image_core/           # Image decoding, thresholding, cropping
│   ├── segmentation/         # Glyph segmentation from sample images
│   ├── font_engine/          # Vectorization, reconstruction, export
│   ├── font_source/          # UFO package generation (norad)
│   ├── ocr/                  # OCR adapter traits
│   ├── worker/               # Async job processor
│   └── cli/                  # CLI for migrations and seeding
├── fixtures/
│   ├── samples/              # Golden test sample images
│   └── fonts/                # Golden export artifacts
├── docs/                     # Architecture and design docs
├── Cargo.toml                # Workspace root
└── .gitignore
```

## Binaries

| Binary | Command | Purpose |
|--------|---------|---------|
| `font-lab-api` | `cargo run --bin font-lab-api` | HTTP API server on `:8000` |
| `font-lab-worker` | `cargo run --bin font-lab-worker` | Background job processor |
| `font-lab-cli` | `cargo run --bin font-lab-cli` | Migrations and admin tasks |

### CLI commands

```bash
# Run database migrations
cargo run --bin font-lab-cli -- migrate

# Seed taxonomy dimensions and terms
cargo run --bin font-lab-cli -- seed-taxonomy
```

## API endpoints

All routes are under `/api/v1`.

### Samples

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/samples` | Upload image (multipart) |
| `GET` | `/api/v1/samples` | List samples (`?page=&per_page=`) |
| `GET` | `/api/v1/samples/:id` | Get sample |
| `PATCH` | `/api/v1/samples/:id` | Update sample metadata |
| `DELETE` | `/api/v1/samples/:id` | Delete sample |
| `POST` | `/api/v1/samples/:id/segment` | Trigger glyph segmentation |

### Glyphs

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/samples/:id/glyphs` | List glyphs for a sample |
| `GET` | `/api/v1/samples/:id/glyphs/:gid` | Get glyph |
| `PATCH` | `/api/v1/samples/:id/glyphs/:gid` | Update glyph (label, status) |
| `DELETE` | `/api/v1/samples/:id/glyphs/:gid` | Delete glyph |
| `GET` | `/api/v1/samples/:id/glyphs/:gid/outline` | Get SVG outline |

### Catalog

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/catalog` | Browse catalog (`?page=&per_page=`) |
| `GET` | `/api/v1/catalog/search` | Search (`?q=`) |
| `GET` | `/api/v1/catalog/:id/similar` | Find similar fonts |

### Keys

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/keys` | Create API key |
| `GET` | `/api/v1/keys` | List API keys |
| `POST` | `/api/v1/keys/:id/revoke` | Revoke API key |

### Taxonomy

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/taxonomy` | List taxonomy dimensions and terms |

## Tech stack

| Layer | Technology |
|-------|------------|
| HTTP server | Rust · axum · tokio |
| Database | SQLite (sqlx, WAL mode) |
| Image processing | image crate · custom segmentation |
| Font engineering | write-fonts · read-fonts · norad (UFO) |
| Frontend | React 19 · TypeScript · Vite |

### Glyphs

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/samples/{id}/segment` | Run glyph segmentation; returns extracted glyphs |
| `GET` | `/api/samples/{id}/glyphs` | List glyphs for a sample (ordered by position) |
| `GET` | `/api/glyphs/{glyph_id}` | Get single glyph |
| `PATCH` | `/api/glyphs/{glyph_id}` | Update label, bounding box, or verified flag |
| `DELETE` | `/api/glyphs/{glyph_id}` | Delete glyph record and crop file |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, coding guidelines, and pull request requirements.

## License

This project is licensed under the [MIT License](LICENSE).
