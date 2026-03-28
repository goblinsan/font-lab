"""Font catalog API – search and structured metadata endpoints.

Exposes three endpoints:

* ``GET /api/catalog/``         — list all catalog entries (with previews)
* ``GET /api/catalog/search``   — query fonts by metadata and traits (#15)
* ``GET /api/catalog/{id}``     — structured font data and preview  (#16)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FontSample, Glyph
from app.schemas import CatalogEntryResponse

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


def _preview_url(filename: str) -> str:
    return f"/uploads/{filename}"


def _glyph_counts(db: Session, sample_ids: list[int]) -> dict[int, int]:
    """Return a mapping of sample_id → glyph count fetched in one query."""
    if not sample_ids:
        return {}
    rows = (
        db.query(Glyph.sample_id, func.count(Glyph.id))
        .filter(Glyph.sample_id.in_(sample_ids))
        .group_by(Glyph.sample_id)
        .all()
    )
    return {sample_id: count for sample_id, count in rows}


def _to_catalog_entry(sample: FontSample, glyph_count: int) -> CatalogEntryResponse:
    return CatalogEntryResponse(
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
        preview_url=_preview_url(sample.filename),
        glyph_count=glyph_count,
    )


@router.get("/", response_model=list[CatalogEntryResponse], summary="List font catalog")
def list_catalog(db: Session = Depends(get_db)):
    """Return all font catalog entries with preview URLs and glyph counts."""
    samples = db.query(FontSample).all()
    counts = _glyph_counts(db, [s.id for s in samples])
    return [_to_catalog_entry(s, counts.get(s.id, 0)) for s in samples]


@router.get(
    "/search",
    response_model=list[CatalogEntryResponse],
    summary="Search fonts by metadata and traits",
)
def search_catalog(
    q: str | None = Query(None, description="Full-text search across name, category, style, theme, and notes"),
    font_name: str | None = Query(None),
    font_category: str | None = Query(None),
    style: str | None = Query(None),
    theme: str | None = Query(None),
    tag: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Query the font catalog by metadata and traits.

    Parameters
    ----------
    q:
        Optional free-text query matched case-insensitively against
        ``font_name``, ``font_category``, ``style``, ``theme``, and ``notes``.
    font_name, font_category, style, theme:
        Narrow filters applied in addition to (or instead of) ``q``.
    tag:
        Filter to samples whose tag list contains this value (case-insensitive).
    """
    query = db.query(FontSample)

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                FontSample.font_name.ilike(like),
                FontSample.font_category.ilike(like),
                FontSample.style.ilike(like),
                FontSample.theme.ilike(like),
                FontSample.notes.ilike(like),
            )
        )
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

    counts = _glyph_counts(db, [s.id for s in samples])
    return [_to_catalog_entry(s, counts.get(s.id, 0)) for s in samples]


@router.get(
    "/{sample_id}",
    response_model=CatalogEntryResponse,
    summary="Get structured font data and preview",
)
def get_catalog_entry(sample_id: int, db: Session = Depends(get_db)):
    """Return structured font metadata and a preview URL for *sample_id*."""
    sample = db.get(FontSample, sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    counts = _glyph_counts(db, [sample.id])
    return _to_catalog_entry(sample, counts.get(sample.id, 0))
