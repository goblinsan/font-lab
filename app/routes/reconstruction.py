"""Font reconstruction engine routes.

Exposes three endpoints:

* ``GET  /api/glyphs/{id}/outline``        — SVG vector outline for a single glyph
* ``POST /api/samples/{id}/reconstruct``   — synthesise missing glyphs (Issue #7)
* ``POST /api/samples/{id}/export``        — export OTF/TTF font file  (Issues #8, #9)
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from sqlalchemy.orm import Session

from app.database import get_db
from app.font_export import export_font
from app.models import FontSample, Glyph
from app.reconstruction import DEFAULT_CHARSET, reconstruct_missing_glyphs
from app.schemas import ExportRequest, GlyphResponse, ReconstructRequest
from app.vectorize import glyph_to_svg

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
GLYPH_SUBDIR = "glyphs"

router = APIRouter(tags=["reconstruction"])

_FONT_MEDIA_TYPES = {
    "ttf": "font/ttf",
    "otf": "font/otf",
}
_ALLOWED_FORMATS = set(_FONT_MEDIA_TYPES.keys())


def _glyph_dir() -> str:
    path = os.path.join(UPLOAD_DIR, GLYPH_SUBDIR)
    os.makedirs(path, exist_ok=True)
    return path


def _to_response(glyph: Glyph) -> GlyphResponse:
    return GlyphResponse(
        id=glyph.id,
        sample_id=glyph.sample_id,
        filename=glyph.filename,
        bbox_x=glyph.bbox_x,
        bbox_y=glyph.bbox_y,
        bbox_w=glyph.bbox_w,
        bbox_h=glyph.bbox_h,
        label=glyph.label,
        verified=glyph.verified,
        synthesized=glyph.synthesized,
        created_at=glyph.created_at,
    )


# ---------------------------------------------------------------------------
# GET /api/glyphs/{id}/outline — SVG vector outline (Issue #8)
# ---------------------------------------------------------------------------

@router.get(
    "/api/glyphs/{glyph_id}/outline",
    response_class=Response,
    summary="Get SVG vector outline for a single glyph",
)
def get_glyph_outline(glyph_id: int, db: Session = Depends(get_db)):
    """Return an SVG document tracing the foreground pixels of *glyph_id*.

    The outline is built via a scanline algorithm: each horizontal run of
    foreground pixels becomes a filled rectangle in the SVG path.
    """
    glyph = db.get(Glyph, glyph_id)
    if not glyph:
        raise HTTPException(status_code=404, detail="Glyph not found")

    crop_path = os.path.join(_glyph_dir(), glyph.filename)
    if not os.path.exists(crop_path):
        raise HTTPException(status_code=404, detail="Glyph image file not found on disk")

    try:
        svg = glyph_to_svg(crop_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not vectorise glyph: {exc}") from exc

    return Response(content=svg, media_type="image/svg+xml")


# ---------------------------------------------------------------------------
# POST /api/samples/{id}/reconstruct — infer missing glyphs (Issue #7)
# ---------------------------------------------------------------------------

@router.post(
    "/api/samples/{sample_id}/reconstruct",
    response_model=list[GlyphResponse],
    status_code=201,
    summary="Synthesise missing glyphs for a font sample",
)
def reconstruct_sample(
    sample_id: int,
    payload: ReconstructRequest = ReconstructRequest(),
    db: Session = Depends(get_db),
):
    """Infer and create synthetic glyph crops for characters absent from the
    sample's labelled glyph set.

    Existing synthesised glyphs for this sample are removed first so that
    re-running reconstruction always reflects the current labelled set.

    Each synthesised glyph is marked ``synthesized=True`` and can be
    reviewed or corrected via the standard glyph update endpoint.
    """
    if not db.get(FontSample, sample_id):
        raise HTTPException(status_code=404, detail="Sample not found")

    # Remove previously synthesised glyphs for this sample
    existing_synth: list[Glyph] = (
        db.query(Glyph)
        .filter(Glyph.sample_id == sample_id, Glyph.synthesized.is_(True))
        .all()
    )
    for g in existing_synth:
        crop_path = os.path.join(_glyph_dir(), g.filename)
        if os.path.exists(crop_path):
            os.remove(crop_path)
        db.delete(g)
    db.flush()

    all_glyphs: list[Glyph] = (
        db.query(Glyph).filter(Glyph.sample_id == sample_id).all()
    )

    charset = payload.charset
    new_glyphs = reconstruct_missing_glyphs(
        sample_id, all_glyphs, _glyph_dir(), charset
    )

    for g in new_glyphs:
        db.add(g)
    db.commit()
    for g in new_glyphs:
        db.refresh(g)

    return [_to_response(g) for g in new_glyphs]


# ---------------------------------------------------------------------------
# POST /api/samples/{id}/export — generate font file (Issues #8, #9)
# ---------------------------------------------------------------------------

@router.post(
    "/api/samples/{sample_id}/export",
    response_class=Response,
    summary="Export an OTF or TTF font file from a sample's glyphs",
)
def export_sample_font(
    sample_id: int,
    payload: ExportRequest = ExportRequest(),
    db: Session = Depends(get_db),
):
    """Build and return a font file containing all labelled glyphs.

    Each labelled glyph crop is vectorised (scanline → filled rectangles)
    and embedded as an outline.  Glyphs without a label are skipped.

    Parameters
    ----------
    format:
        ``"ttf"`` (default) or ``"otf"``.
    font_name:
        Font family name written into the ``name`` table.
    style_name:
        Style sub-family name (default ``"Regular"``).
    """
    sample = db.get(FontSample, sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    fmt = payload.format.lower()
    if fmt not in _ALLOWED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{fmt}'. Allowed: {sorted(_ALLOWED_FORMATS)}",
        )

    glyphs: list[Glyph] = (
        db.query(Glyph).filter(Glyph.sample_id == sample_id).all()
    )

    font_name = payload.font_name or sample.font_name or "ReconstructedFont"
    style_name = payload.style_name or "Regular"

    try:
        font_bytes = export_font(font_name, style_name, glyphs, _glyph_dir(), format=fmt)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Font generation failed: {exc}") from exc

    media_type = _FONT_MEDIA_TYPES[fmt]
    filename = f"{font_name.replace(' ', '_')}-{style_name.replace(' ', '_')}.{fmt}"
    return Response(
        content=font_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
