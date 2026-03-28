"""Integration adapters for Vizail and kulrs.

Exposes two endpoints:

* ``GET /api/integrations/vizail``  — font catalog in Vizail-compatible format (#17)
* ``GET /api/integrations/kulrs``   — font catalog in kulrs-compatible format  (#17)
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FontSample, Glyph

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


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


@router.get("/vizail", summary="Font catalog in Vizail-compatible format")
def vizail_catalog(db: Session = Depends(get_db)) -> dict:
    """Return the full font catalog formatted for the Vizail visualisation tool.

    Response shape::

        {
            "fonts": [
                {
                    "id": 1,
                    "name": "Helvetica",
                    "category": "sans-serif",
                    "style": "Sans-Serif",
                    "theme": "Modern",
                    "tags": ["bold"],
                    "preview_url": "/uploads/abc123.png",
                    "glyph_count": 26
                },
                ...
            ]
        }
    """
    samples = db.query(FontSample).all()
    counts = _glyph_counts(db, [s.id for s in samples])
    fonts = [
        {
            "id": sample.id,
            "name": sample.font_name,
            "category": sample.font_category,
            "style": sample.style,
            "theme": sample.theme,
            "tags": sample.tags,
            "preview_url": _preview_url(sample.filename),
            "glyph_count": counts.get(sample.id, 0),
        }
        for sample in samples
    ]
    return {"fonts": fonts}


@router.get("/kulrs", summary="Font catalog in kulrs-compatible format")
def kulrs_catalog(db: Session = Depends(get_db)) -> list:
    """Return the full font catalog formatted for the kulrs integration.

    Response shape::

        [
            {
                "id": 1,
                "name": "Helvetica",
                "traits": {
                    "category": "sans-serif",
                    "style": "Sans-Serif",
                    "theme": "Modern"
                },
                "tags": ["bold"],
                "preview_url": "/uploads/abc123.png"
            },
            ...
        ]
    """
    samples = db.query(FontSample).all()
    result = []
    for sample in samples:
        result.append(
            {
                "id": sample.id,
                "name": sample.font_name,
                "traits": {
                    "category": sample.font_category,
                    "style": sample.style,
                    "theme": sample.theme,
                },
                "tags": sample.tags,
                "preview_url": _preview_url(sample.filename),
            }
        )
    return result
