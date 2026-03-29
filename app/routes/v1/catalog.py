"""Versioned font catalog API – v1.

Exposes paginated, sortable, and filterable endpoints under ``/api/v1/``:

* ``GET /api/v1/fonts``            — paginated list with filtering and sorting
* ``GET /api/v1/fonts/search``     — semantic search by text, tags, and traits
* ``GET /api/v1/fonts/{id}``       — full metadata record with preview URL
* ``GET /api/v1/fonts/{id}/similar`` — similarity-ranked related fonts
* ``GET /api/v1/fonts/{id}/preview`` — embeddable preview / specimen config
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth import get_api_key
from app.database import get_db
from app.models import ApiKey, FontSample, Glyph
from app.schemas import (
    CatalogEntryResponse,
    PreviewConfigResponse,
    SimilarFontEntry,
)

router = APIRouter(prefix="/api/v1/fonts", tags=["v1 catalog"])

_SORT_FIELDS = {
    "font_name": FontSample.font_name,
    "uploaded_at": FontSample.uploaded_at,
    "style": FontSample.style,
    "theme": FontSample.theme,
    "era": FontSample.era,
    "confidence": FontSample.confidence,
}


def _preview_url(filename: str) -> str:
    return f"/uploads/{filename}"


def _glyph_counts(db: Session, sample_ids: list[int]) -> dict[int, int]:
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
        genre=sample.genre,
        theme=sample.theme,
        era=sample.era,
        provenance=sample.provenance,
        confidence=sample.confidence,
        notes=sample.notes,
        source=sample.source,
        restoration_notes=sample.restoration_notes,
        tags=sample.tags,
        file_size=sample.file_size,
        content_type=sample.content_type,
        uploaded_at=sample.uploaded_at,
        preview_url=_preview_url(sample.filename),
        glyph_count=glyph_count,
        origin_context=sample.origin_context,
        source_type=sample.source_type,
        restoration_status=sample.restoration_status,
        rights_status=sample.rights_status,
        rights_notes=sample.rights_notes,
        completeness=sample.completeness,
        moods=sample.moods,
        use_cases=sample.use_cases,
        construction_traits=sample.construction_traits,
        visual_traits=sample.visual_traits,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/fonts – paginated list
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=dict,
    summary="List fonts (v1) – paginated, sortable, filterable",
)
def list_fonts_v1(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: Literal["font_name", "uploaded_at", "style", "theme", "era", "confidence"] = Query(
        "uploaded_at", description="Field to sort by"
    ),
    order: Literal["asc", "desc"] = Query("desc", description="Sort direction"),
    font_category: str | None = Query(None),
    style: str | None = Query(None),
    genre: str | None = Query(None),
    theme: str | None = Query(None),
    era: str | None = Query(None),
    origin_context: str | None = Query(None),
    source_type: str | None = Query(None),
    restoration_status: str | None = Query(None),
    rights_status: str | None = Query(None),
    db: Session = Depends(get_db),
    _key: ApiKey | None = Depends(get_api_key),
):
    """Return a paginated list of all font catalog entries.

    Supports optional filtering by ``font_category``, ``style``, ``genre``,
    ``theme``, ``era``, ``origin_context``, ``source_type``,
    ``restoration_status``, and ``rights_status``, plus server-side sorting
    and pagination.

    Response shape::

        {
            "total": 42,
            "page": 1,
            "per_page": 20,
            "items": [ ... ]
        }
    """
    query = db.query(FontSample)

    if font_category:
        query = query.filter(FontSample.font_category.ilike(f"%{font_category}%"))
    if style:
        query = query.filter(FontSample.style.ilike(f"%{style}%"))
    if genre:
        query = query.filter(FontSample.genre.ilike(f"%{genre}%"))
    if theme:
        query = query.filter(FontSample.theme.ilike(f"%{theme}%"))
    if era:
        query = query.filter(FontSample.era.ilike(f"%{era}%"))
    if origin_context:
        query = query.filter(FontSample.origin_context.ilike(f"%{origin_context}%"))
    if source_type:
        query = query.filter(FontSample.source_type.ilike(f"%{source_type}%"))
    if restoration_status:
        query = query.filter(FontSample.restoration_status.ilike(f"%{restoration_status}%"))
    if rights_status:
        query = query.filter(FontSample.rights_status.ilike(f"%{rights_status}%"))

    sort_col = _SORT_FIELDS.get(sort, FontSample.uploaded_at)
    query = query.order_by(sort_col.asc() if order == "asc" else sort_col.desc())

    total = query.count()
    offset = (page - 1) * per_page
    samples = query.offset(offset).limit(per_page).all()

    counts = _glyph_counts(db, [s.id for s in samples])
    items = [_to_catalog_entry(s, counts.get(s.id, 0)) for s in samples]

    return {"total": total, "page": page, "per_page": per_page, "items": items}


# ---------------------------------------------------------------------------
# GET /api/v1/fonts/search – semantic search
# ---------------------------------------------------------------------------

@router.get(
    "/search",
    response_model=dict,
    summary="Semantic font search (v1)",
)
def search_fonts_v1(
    q: str | None = Query(None, description="Free-text search across name, notes, style, theme, era, tags"),
    font_name: str | None = Query(None),
    font_category: str | None = Query(None),
    style: str | None = Query(None),
    genre: str | None = Query(None),
    theme: str | None = Query(None),
    era: str | None = Query(None),
    origin_context: str | None = Query(None),
    source_type: str | None = Query(None),
    restoration_status: str | None = Query(None),
    rights_status: str | None = Query(None),
    tag: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort: Literal["font_name", "uploaded_at", "style", "theme", "era", "confidence"] = Query("uploaded_at"),
    order: Literal["asc", "desc"] = Query("desc"),
    db: Session = Depends(get_db),
    _key: ApiKey | None = Depends(get_api_key),
):
    """Search the font catalog by text, tags, themes, visual traits, and era.

    ``q`` is matched case-insensitively against ``font_name``, ``font_category``,
    ``style``, ``genre``, ``theme``, ``era``, ``origin_context``, and ``notes``.
    Narrower filters can be combined with or without ``q``.

    Response shape::

        {
            "total": 5,
            "page": 1,
            "per_page": 20,
            "items": [ ... ]
        }
    """
    query = db.query(FontSample)

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                FontSample.font_name.ilike(like),
                FontSample.font_category.ilike(like),
                FontSample.style.ilike(like),
                FontSample.genre.ilike(like),
                FontSample.theme.ilike(like),
                FontSample.era.ilike(like),
                FontSample.origin_context.ilike(like),
                FontSample.notes.ilike(like),
            )
        )
    if font_name:
        query = query.filter(FontSample.font_name.ilike(f"%{font_name}%"))
    if font_category:
        query = query.filter(FontSample.font_category.ilike(f"%{font_category}%"))
    if style:
        query = query.filter(FontSample.style.ilike(f"%{style}%"))
    if genre:
        query = query.filter(FontSample.genre.ilike(f"%{genre}%"))
    if theme:
        query = query.filter(FontSample.theme.ilike(f"%{theme}%"))
    if era:
        query = query.filter(FontSample.era.ilike(f"%{era}%"))
    if origin_context:
        query = query.filter(FontSample.origin_context.ilike(f"%{origin_context}%"))
    if source_type:
        query = query.filter(FontSample.source_type.ilike(f"%{source_type}%"))
    if restoration_status:
        query = query.filter(FontSample.restoration_status.ilike(f"%{restoration_status}%"))
    if rights_status:
        query = query.filter(FontSample.rights_status.ilike(f"%{rights_status}%"))
    if tag:
        # Tags are stored as JSON text; use a LIKE filter to push filtering
        # to the database before loading rows into memory.
        query = query.filter(FontSample._tags.ilike(f"%{tag}%"))

    sort_col = _SORT_FIELDS.get(sort, FontSample.uploaded_at)
    query = query.order_by(sort_col.asc() if order == "asc" else sort_col.desc())

    total = query.count()
    offset = (page - 1) * per_page
    page_samples = query.offset(offset).limit(per_page).all()

    counts = _glyph_counts(db, [s.id for s in page_samples])
    items = [_to_catalog_entry(s, counts.get(s.id, 0)) for s in page_samples]

    return {"total": total, "page": page, "per_page": per_page, "items": items}


# ---------------------------------------------------------------------------
# GET /api/v1/fonts/{id} – single entry
# ---------------------------------------------------------------------------

@router.get(
    "/{font_id}",
    response_model=CatalogEntryResponse,
    summary="Get full font metadata and preview (v1)",
    responses={404: {"description": "Font not found"}},
)
def get_font_v1(
    font_id: int,
    db: Session = Depends(get_db),
    _key: ApiKey | None = Depends(get_api_key),
):
    """Return the full metadata record and a preview URL for *font_id*."""
    sample = db.get(FontSample, font_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Font not found")
    counts = _glyph_counts(db, [sample.id])
    return _to_catalog_entry(sample, counts.get(sample.id, 0))


# ---------------------------------------------------------------------------
# GET /api/v1/fonts/{id}/similar – similarity ranking
# ---------------------------------------------------------------------------

def _similarity_score(target: FontSample, candidate: FontSample) -> float:
    """Compute a [0, 1] similarity score between two FontSample records.

    Weights:
    - style match           → 0.25
    - genre match           → 0.10
    - theme match           → 0.20
    - font_category match   → 0.15
    - era match             → 0.05
    - shared tags           → up to 0.10 (Jaccard)
    - shared moods          → up to 0.05 (Jaccard)
    - shared visual_traits  → up to 0.10 (Jaccard)
    """
    score = 0.0
    if target.style and candidate.style and target.style.lower() == candidate.style.lower():
        score += 0.25
    if target.genre and candidate.genre and target.genre.lower() == candidate.genre.lower():
        score += 0.10
    if target.theme and candidate.theme and target.theme.lower() == candidate.theme.lower():
        score += 0.20
    if (
        target.font_category
        and candidate.font_category
        and target.font_category.lower() == candidate.font_category.lower()
    ):
        score += 0.15
    if target.era and candidate.era and target.era.lower() == candidate.era.lower():
        score += 0.05
    # Tag Jaccard similarity
    t_tags = set(t.lower() for t in target.tags)
    c_tags = set(t.lower() for t in candidate.tags)
    if t_tags or c_tags:
        score += 0.10 * len(t_tags & c_tags) / len(t_tags | c_tags)
    # Mood Jaccard similarity
    t_moods = set(m.lower() for m in target.moods)
    c_moods = set(m.lower() for m in candidate.moods)
    if t_moods or c_moods:
        score += 0.05 * len(t_moods & c_moods) / len(t_moods | c_moods)
    # Visual trait Jaccard similarity
    t_vt = set(v.lower() for v in target.visual_traits)
    c_vt = set(v.lower() for v in candidate.visual_traits)
    if t_vt or c_vt:
        score += 0.10 * len(t_vt & c_vt) / len(t_vt | c_vt)
    return round(score, 4)


@router.get(
    "/{font_id}/similar",
    response_model=list[SimilarFontEntry],
    summary="Find visually and stylistically similar fonts (v1)",
    responses={404: {"description": "Font not found"}},
)
def similar_fonts(
    font_id: int,
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    db: Session = Depends(get_db),
    _key: ApiKey | None = Depends(get_api_key),
):
    """Return fonts ranked by similarity to *font_id*.

    Similarity is computed from matching style, theme, category, era, and shared
    tags using a weighted scoring formula.  Only fonts with a score ≥ *min_score*
    are included.
    """
    target = db.get(FontSample, font_id)
    if not target:
        raise HTTPException(status_code=404, detail="Font not found")

    candidates = db.query(FontSample).filter(FontSample.id != font_id).all()
    scored = [
        (c, _similarity_score(target, c))
        for c in candidates
    ]
    scored = [(c, s) for c, s in scored if s >= min_score]
    scored.sort(key=lambda x: x[1], reverse=True)

    return [
        SimilarFontEntry(
            id=c.id,
            font_name=c.font_name,
            font_category=c.font_category,
            style=c.style,
            genre=c.genre,
            theme=c.theme,
            era=c.era,
            tags=c.tags,
            moods=c.moods,
            visual_traits=c.visual_traits,
            preview_url=_preview_url(c.filename),
            similarity_score=s,
        )
        for c, s in scored[:limit]
    ]


# ---------------------------------------------------------------------------
# GET /api/v1/fonts/{id}/preview – embeddable preview config
# ---------------------------------------------------------------------------

@router.get(
    "/{font_id}/preview",
    response_model=PreviewConfigResponse,
    summary="Get embeddable preview and specimen configuration (v1)",
    responses={404: {"description": "Font not found"}},
)
def font_preview_config(
    font_id: int,
    db: Session = Depends(get_db),
    _key: ApiKey | None = Depends(get_api_key),
):
    """Return a render configuration for *font_id*.

    Includes the preview image URL, a specimen URL for the print-preview
    endpoint, an embeddable ``<iframe>`` URL, and the set of available labelled
    characters.
    """
    sample = db.get(FontSample, font_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Font not found")

    glyphs = (
        db.query(Glyph)
        .filter(Glyph.sample_id == font_id, Glyph.label.isnot(None))
        .all()
    )
    available_chars = sorted({g.label for g in glyphs if g.label})

    return PreviewConfigResponse(
        sample_id=font_id,
        font_name=sample.font_name,
        preview_url=_preview_url(sample.filename),
        specimen_url=f"/api/samples/{font_id}/print-preview",
        embed_url=f"/api/samples/{font_id}/print-preview?font_size=48",
        available_chars=available_chars,
        suggested_text="The quick brown fox",
    )
