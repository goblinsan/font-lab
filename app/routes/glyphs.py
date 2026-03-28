"""Glyph segmentation and correction routes."""

import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FontSample, Glyph
from app.schemas import GlyphResponse, GlyphUpdate
from app.segmentation import segment_glyphs

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
GLYPH_SUBDIR = "glyphs"

router = APIRouter(tags=["glyphs"])


def _glyph_dir() -> str:
    """Return (and create) the directory used to store glyph crop images."""
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
# Segmentation trigger
# ---------------------------------------------------------------------------

@router.post(
    "/api/samples/{sample_id}/segment",
    response_model=list[GlyphResponse],
    status_code=201,
    summary="Segment glyphs from a font sample",
)
def segment_sample(sample_id: int, db: Session = Depends(get_db)):
    """Run glyph segmentation on the uploaded image for *sample_id*.

    Existing glyphs for this sample are deleted before the new run so that
    re-running segmentation always reflects the current image.
    """
    sample = db.get(FontSample, sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    image_path = os.path.join(UPLOAD_DIR, sample.filename)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found on disk")

    # Remove previously extracted glyphs for this sample
    existing: list[Glyph] = db.query(Glyph).filter(Glyph.sample_id == sample_id).all()
    for g in existing:
        crop_path = os.path.join(_glyph_dir(), g.filename)
        if os.path.exists(crop_path):
            os.remove(crop_path)
        db.delete(g)
    db.flush()

    try:
        glyph_info_list = segment_glyphs(image_path, _glyph_dir())
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not process image: {exc}") from exc

    glyphs: list[Glyph] = []
    for info in glyph_info_list:
        glyph = Glyph(
            sample_id=sample_id,
            filename=info["filename"],
            bbox_x=info["bbox_x"],
            bbox_y=info["bbox_y"],
            bbox_w=info["bbox_w"],
            bbox_h=info["bbox_h"],
        )
        db.add(glyph)
        glyphs.append(glyph)

    db.commit()
    for g in glyphs:
        db.refresh(g)

    return [_to_response(g) for g in glyphs]


# ---------------------------------------------------------------------------
# List glyphs for a sample
# ---------------------------------------------------------------------------

@router.get(
    "/api/samples/{sample_id}/glyphs",
    response_model=list[GlyphResponse],
    summary="List extracted glyphs for a font sample",
)
def list_glyphs(sample_id: int, db: Session = Depends(get_db)):
    """Return all glyphs belonging to *sample_id*, ordered by position."""
    if not db.get(FontSample, sample_id):
        raise HTTPException(status_code=404, detail="Sample not found")
    glyphs = (
        db.query(Glyph)
        .filter(Glyph.sample_id == sample_id)
        .order_by(Glyph.bbox_y, Glyph.bbox_x)
        .all()
    )
    return [_to_response(g) for g in glyphs]


# ---------------------------------------------------------------------------
# Single glyph CRUD
# ---------------------------------------------------------------------------

@router.get(
    "/api/glyphs/{glyph_id}",
    response_model=GlyphResponse,
    summary="Get a single glyph",
)
def get_glyph(glyph_id: int, db: Session = Depends(get_db)):
    glyph = db.get(Glyph, glyph_id)
    if not glyph:
        raise HTTPException(status_code=404, detail="Glyph not found")
    return _to_response(glyph)


@router.patch(
    "/api/glyphs/{glyph_id}",
    response_model=GlyphResponse,
    summary="Update glyph label, bounding box, or verified flag",
)
def update_glyph(glyph_id: int, payload: GlyphUpdate, db: Session = Depends(get_db)):
    """Apply a partial update to a glyph (label, bbox, or verified status)."""
    glyph = db.get(Glyph, glyph_id)
    if not glyph:
        raise HTTPException(status_code=404, detail="Glyph not found")

    if payload.label is not None:
        glyph.label = payload.label
    if payload.bbox_x is not None:
        glyph.bbox_x = payload.bbox_x
    if payload.bbox_y is not None:
        glyph.bbox_y = payload.bbox_y
    if payload.bbox_w is not None:
        glyph.bbox_w = payload.bbox_w
    if payload.bbox_h is not None:
        glyph.bbox_h = payload.bbox_h
    if payload.verified is not None:
        glyph.verified = payload.verified

    db.commit()
    db.refresh(glyph)
    return _to_response(glyph)


@router.delete(
    "/api/glyphs/{glyph_id}",
    status_code=204,
    summary="Delete a glyph",
)
def delete_glyph(glyph_id: int, db: Session = Depends(get_db)):
    """Delete a glyph record and its crop image file."""
    glyph = db.get(Glyph, glyph_id)
    if not glyph:
        raise HTTPException(status_code=404, detail="Glyph not found")

    crop_path = os.path.join(_glyph_dir(), glyph.filename)
    if os.path.exists(crop_path):
        os.remove(crop_path)

    db.delete(glyph)
    db.commit()
