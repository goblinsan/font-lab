# font-lab

A web application for ingesting, tagging, browsing, and curating font sample images (scans or photos).

## Features

- **Upload** font sample images (PNG, JPEG, GIF, WebP, TIFF)
- **Tag & annotate** samples with font name, category, comma-separated tags, and free-form notes
- **Provenance tracking** — record the original source and any restoration notes for each sample
- **Browse** the gallery with live filtering by font name, category, or tag
- **Update** metadata for any existing sample
- **Delete** samples (removes the file and the DB record)
- **Segment glyphs** — extract individual characters from a sample image using a projection-histogram algorithm (Pillow only, no OpenCV dependency)
- **Manual correction UI** — modal panel per sample with:
  - Bounding-box overlays on the source image
  - Glyph-crop grid with inline label editing
  - One-click verify / delete per glyph
  - Re-run segmentation at any time
- Auto-generated REST API docs at `/docs`

## Tech stack

| Layer    | Technology |
|----------|-----------|
| Backend  | Python · FastAPI · SQLAlchemy · SQLite |
| Image processing | Pillow |
| Frontend | Vanilla HTML / CSS / JavaScript |
| Tests    | pytest · HTTPX (via FastAPI TestClient) |

## Quick start

```bash
# 1. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the development server
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.  
Interactive API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

## Running tests

```bash
pytest tests/ -v
```

## Project structure

```
font-lab/
├── app/
│   ├── main.py          # FastAPI application entry point
│   ├── database.py      # SQLAlchemy engine & session
│   ├── models.py        # ORM models (FontSample, Glyph)
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── segmentation.py  # Projection-histogram glyph extraction
│   ├── routes/
│   │   ├── images.py    # Upload, list, get, update, delete sample endpoints
│   │   └── glyphs.py    # Segment, list, get, update, delete glyph endpoints
│   └── static/
│       └── index.html   # Single-page frontend (gallery + correction panel)
├── uploads/             # Uploaded image files (git-ignored)
│   └── glyphs/          # Extracted glyph crop PNGs (git-ignored)
├── tests/
│   ├── conftest.py      # Fixtures (in-memory DB, temp upload dir)
│   ├── test_images.py   # API tests for font sample endpoints
│   └── test_glyphs.py   # API tests for glyph endpoints
├── CONTRIBUTING.md
├── LICENSE
├── requirements.txt
└── .gitignore
```

## API reference

### Font samples

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/samples/` | Upload image + metadata |
| `GET` | `/api/samples/` | List all samples (supports `?font_name=`, `?font_category=`, `?tag=`) |
| `GET` | `/api/samples/{id}` | Get single sample |
| `PATCH` | `/api/samples/{id}` | Update metadata |
| `DELETE` | `/api/samples/{id}` | Delete sample |

#### Provenance fields

Every sample record exposes two provenance fields that can be set on upload or via `PATCH`:

| Field | Type | Description |
|-------|------|-------------|
| `source` | `string \| null` | Origin of the image (URL, archive name, publication, etc.) |
| `restoration_notes` | `string \| null` | Description of any processing or restoration applied to the image |

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
