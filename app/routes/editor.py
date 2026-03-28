"""Editor and QA tools.

Exposes endpoints for:

* ``GET /api/samples/{id}/compare``       — source vs. generated comparison (Issue #19)
* ``GET /api/samples/{id}/print-preview`` — decal / print preview            (Issue #21)
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FontSample, Glyph
from app.schemas import GlyphCompareEntry

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")

router = APIRouter(tags=["editor"])


# ---------------------------------------------------------------------------
# GET /api/samples/{id}/compare — source vs. generated (Issue #19)
# ---------------------------------------------------------------------------

@router.get(
    "/api/samples/{sample_id}/compare",
    response_model=list[GlyphCompareEntry],
    summary="Compare source and generated glyphs for a font sample",
)
def compare_sample(sample_id: int, db: Session = Depends(get_db)):
    """Return comparison data for every glyph in the sample.

    Each entry pairs the source crop image URL with the vector outline URL so
    the caller can render them side-by-side for QA purposes.
    """
    if not db.get(FontSample, sample_id):
        raise HTTPException(status_code=404, detail="Sample not found")

    glyphs = (
        db.query(Glyph)
        .filter(Glyph.sample_id == sample_id)
        .order_by(Glyph.bbox_y, Glyph.bbox_x)
        .all()
    )

    return [
        GlyphCompareEntry(
            id=g.id,
            label=g.label,
            source_url=f"/uploads/glyphs/{g.filename}",
            outline_url=f"/api/glyphs/{g.id}/outline",
            verified=g.verified,
            synthesized=g.synthesized,
        )
        for g in glyphs
    ]


# ---------------------------------------------------------------------------
# GET /api/samples/{id}/print-preview — decal/print preview (Issue #21)
# ---------------------------------------------------------------------------

@router.get(
    "/api/samples/{sample_id}/print-preview",
    response_class=HTMLResponse,
    summary="Generate a decal and print preview for a font sample",
)
def print_preview(
    sample_id: int,
    text: str = Query("The quick brown fox", description="Text to render in the preview"),
    font_size: int = Query(48, ge=8, le=200, description="Font size in pixels"),
    db: Session = Depends(get_db),
):
    """Return an HTML page that simulates real-world outputs (decal, print).

    Renders *text* using the labelled glyph images extracted from the sample.
    Characters without a matching labelled glyph are shown as a placeholder.
    Characters can include uppercase and lowercase letters, digits, and spaces.
    """
    sample = db.get(FontSample, sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    glyphs = (
        db.query(Glyph)
        .filter(Glyph.sample_id == sample_id, Glyph.label.isnot(None))
        .all()
    )

    # Build a char → glyph URL mapping (last labelled glyph wins per char)
    char_map: dict[str, str] = {}
    for g in glyphs:
        if g.label:
            char_map[g.label] = f"/uploads/glyphs/{g.filename}"

    font_name = sample.font_name or sample.original_filename
    space_width = font_size // 3

    def _render_char(ch: str) -> str:
        if ch == " ":
            return (
                f'<span class="sp-space" style="display:inline-block;'
                f'width:{space_width}px"></span>'
            )
        url = char_map.get(ch)
        if url:
            return (
                f'<img class="sp-char" src="{url}" alt="{ch}" '
                f'style="height:{font_size}px;width:auto;'
                f'vertical-align:bottom;image-rendering:pixelated" />'
            )
        return (
            f'<span class="sp-missing" style="display:inline-flex;'
            f'align-items:center;justify-content:center;'
            f'height:{font_size}px;width:{font_size * 2 // 3}px;'
            f'border:1px dashed #ccc;color:#bbb;'
            f'font-size:{font_size // 3}px;vertical-align:bottom">{ch}</span>'
        )

    rendered_text = "".join(_render_char(ch) for ch in text)
    mapped_count = len(char_map)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Print Preview &mdash; {font_name}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: system-ui, sans-serif; background: #f5f4f0; color: #1a1a1a; padding: 2rem; }}
    h1 {{ font-size: 1.2rem; margin-bottom: 1.5rem; color: #333; }}
    .preview-section {{ margin-bottom: 2.5rem; }}
    .preview-section h2 {{
      font-size: .85rem; color: #777; text-transform: uppercase;
      letter-spacing: .06em; margin-bottom: .75rem;
    }}
    .preview-box {{
      background: #fff;
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(0,0,0,.08);
      padding: 2rem;
      display: flex;
      align-items: flex-end;
      flex-wrap: wrap;
      gap: 2px;
      min-height: {font_size + 40}px;
    }}
    .preview-box.dark {{ background: #1a1a2e; }}
    .preview-box.kraft {{ background: #c8a97e; }}
    .sp-missing {{ border-radius: 3px; }}
    .preview-meta {{ font-size: .75rem; color: #999; margin-top: .5rem; }}
    .preview-footer {{ font-size: .75rem; color: #aaa; margin-top: 2rem; }}
  </style>
</head>
<body>
  <h1>Print Preview &mdash; {font_name}</h1>

  <div class="preview-section">
    <h2>White background (label print)</h2>
    <div class="preview-box">{rendered_text}</div>
    <p class="preview-meta">&ldquo;{text}&rdquo; &middot; {font_size}px</p>
  </div>

  <div class="preview-section">
    <h2>Dark background (decal / sticker)</h2>
    <div class="preview-box dark">{rendered_text}</div>
  </div>

  <div class="preview-section">
    <h2>Kraft background (packaging / signage)</h2>
    <div class="preview-box kraft">{rendered_text}</div>
  </div>

  <p class="preview-footer">
    Generated by font-lab &middot; sample #{sample_id}
    &middot; {mapped_count} mapped glyph{"" if mapped_count == 1 else "s"}
  </p>
</body>
</html>"""

    return HTMLResponse(content=html)
