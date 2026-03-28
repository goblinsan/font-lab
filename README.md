# font-lab

A web application for ingesting, tagging, and browsing font sample images (scans or photos).

## Features

- **Upload** font sample images (PNG, JPEG, GIF, WebP, TIFF)
- **Tag & annotate** samples with font name, category, comma-separated tags, and free-form notes
- **Browse** the gallery with live filtering by font name, category, or tag
- **Update** metadata for any existing sample
- **Delete** samples (removes the file and the DB record)
- Auto-generated REST API docs at `/docs`

## Tech stack

| Layer    | Technology |
|----------|-----------|
| Backend  | Python · FastAPI · SQLAlchemy · SQLite |
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
│   ├── models.py        # ORM model (FontSample)
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── routes/
│   │   └── images.py    # Upload, list, get, update, delete endpoints
│   └── static/
│       └── index.html   # Single-page frontend
├── uploads/             # Uploaded image files (git-ignored)
├── tests/
│   ├── conftest.py      # Fixtures (in-memory DB, temp upload dir)
│   └── test_images.py   # API tests
├── requirements.txt
└── .gitignore
```

## API reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/samples/` | Upload image + metadata |
| `GET` | `/api/samples/` | List all samples (supports `?font_name=`, `?font_category=`, `?tag=`) |
| `GET` | `/api/samples/{id}` | Get single sample |
| `PATCH` | `/api/samples/{id}` | Update metadata |
| `DELETE` | `/api/samples/{id}` | Delete sample |
