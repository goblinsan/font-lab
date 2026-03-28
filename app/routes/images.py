"""Image upload and metadata management routes."""

import os
import uuid

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FontSample
from app.schemas import FontSampleResponse, FontSampleUpdate

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/tiff"}

router = APIRouter(prefix="/api/samples", tags=["samples"])


@router.post("/", response_model=FontSampleResponse, status_code=201)
async def upload_sample(
    file: UploadFile = File(...),
    font_name: str | None = Form(None),
    font_category: str | None = Form(None),
    style: str | None = Form(None),
    theme: str | None = Form(None),
    notes: str | None = Form(None),
    source: str | None = Form(None),
    restoration_notes: str | None = Form(None),
    tags: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """Upload a font sample image with optional metadata."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. "
            f"Allowed types: {sorted(ALLOWED_CONTENT_TYPES)}",
        )

    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, unique_filename)

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    async with aiofiles.open(dest_path, "wb") as out:
        content = await file.read()
        await out.write(content)

    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]

    sample = FontSample(
        filename=unique_filename,
        original_filename=file.filename or unique_filename,
        font_name=font_name,
        font_category=font_category,
        style=style,
        theme=theme,
        notes=notes,
        source=source,
        restoration_notes=restoration_notes,
        file_size=len(content),
        content_type=file.content_type,
    )
    sample.tags = tag_list

    db.add(sample)
    db.commit()
    db.refresh(sample)
    return _to_response(sample)


@router.get("/", response_model=list[FontSampleResponse])
def list_samples(
    font_name: str | None = None,
    font_category: str | None = None,
    style: str | None = None,
    theme: str | None = None,
    tag: str | None = None,
    db: Session = Depends(get_db),
):
    """List all uploaded font samples, with optional filtering."""
    query = db.query(FontSample)
    if font_name:
        query = query.filter(FontSample.font_name.ilike(f"%{font_name}%"))
    if font_category:
        query = query.filter(FontSample.font_category.ilike(f"%{font_category}%"))
    if style:
        query = query.filter(FontSample.style.ilike(f"%{style}%"))
    if theme:
        query = query.filter(FontSample.theme.ilike(f"%{theme}%"))
    samples = query.all()
    if tag:
        samples = [s for s in samples if tag.lower() in [t.lower() for t in s.tags]]
    return [_to_response(s) for s in samples]


@router.get("/{sample_id}", response_model=FontSampleResponse)
def get_sample(sample_id: int, db: Session = Depends(get_db)):
    """Retrieve a single font sample by ID."""
    sample = db.get(FontSample, sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return _to_response(sample)


@router.patch("/{sample_id}", response_model=FontSampleResponse)
def update_sample(
    sample_id: int,
    payload: FontSampleUpdate,
    db: Session = Depends(get_db),
):
    """Update metadata for an existing font sample."""
    sample = db.get(FontSample, sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    if payload.font_name is not None:
        sample.font_name = payload.font_name
    if payload.font_category is not None:
        sample.font_category = payload.font_category
    if payload.style is not None:
        sample.style = payload.style
    if payload.theme is not None:
        sample.theme = payload.theme
    if payload.notes is not None:
        sample.notes = payload.notes
    if payload.source is not None:
        sample.source = payload.source
    if payload.restoration_notes is not None:
        sample.restoration_notes = payload.restoration_notes
    if payload.tags is not None:
        sample.tags = payload.tags

    db.commit()
    db.refresh(sample)
    return _to_response(sample)


@router.delete("/{sample_id}", status_code=204)
def delete_sample(sample_id: int, db: Session = Depends(get_db)):
    """Delete a font sample record (and its file)."""
    sample = db.get(FontSample, sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    file_path = os.path.join(UPLOAD_DIR, sample.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(sample)
    db.commit()


def _to_response(sample: FontSample) -> FontSampleResponse:
    return FontSampleResponse(
        id=sample.id,
        filename=sample.filename,
        original_filename=sample.original_filename,
        font_name=sample.font_name,
        font_category=sample.font_category,
        style=sample.style,
        theme=sample.theme,
        notes=sample.notes,
        source=sample.source,
        restoration_notes=sample.restoration_notes,
        tags=sample.tags,
        file_size=sample.file_size,
        content_type=sample.content_type,
        uploaded_at=sample.uploaded_at,
    )
