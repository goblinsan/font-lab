"""Font file export: build OTF or TTF from a sample's labelled glyphs.

Each labelled glyph crop is vectorised (scanline → rectangles) and
embedded as an outline using fontTools' FontBuilder API.  Glyphs without
a label are skipped; glyph crops missing from disk or producing empty
paths are replaced with a simple filled-rectangle .notdef outline.
"""

from __future__ import annotations

import io
import os
from typing import Literal

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

from app.models import Glyph
from app.vectorize import get_glyph_rects

# ---------------------------------------------------------------------------
# Font-level constants
# ---------------------------------------------------------------------------

_UNITS_PER_EM = 1000
_ASCENT = 800
_DESCENT = -200
_CAP_HEIGHT = 700   # target glyph height in font units
_MARGIN = 50        # minimum left/right side bearing

FontFormat = Literal["ttf", "otf"]


# ---------------------------------------------------------------------------
# Internal drawing helpers
# ---------------------------------------------------------------------------

def _notdef_rects() -> list[tuple[int, int, int, int]]:
    """Return a simple filled rectangle used as the .notdef outline."""
    return [(_MARGIN, 0, _CAP_HEIGHT // 2 + _MARGIN, _CAP_HEIGHT)]


def _pixel_rects_to_font_rects(
    pixel_rects: list[tuple[int, int, int, int]],
    px_w: int,
    px_h: int,
) -> tuple[list[tuple[int, int, int, int]], int]:
    """Convert pixel-space scanline rects to font-unit rects.

    Parameters
    ----------
    pixel_rects:
        Rects in pixel coordinates as ``(x0, y_top, x1, y_bot)`` where
        *y* increases downward.
    px_w, px_h:
        Pixel dimensions of the source glyph crop.

    Returns
    -------
    ``(font_rects, advance_width)`` where each font rect is
    ``(x0, y_bot, x1, y_top)`` in font units (y increases upward).
    """
    if px_h == 0:
        return [], _CAP_HEIGHT // 2 + _MARGIN * 2

    scale = _CAP_HEIGHT / px_h
    font_rects: list[tuple[int, int, int, int]] = []

    for x0, y_top, x1, y_bot in pixel_rects:
        fx0 = round(x0 * scale) + _MARGIN
        fx1 = round(x1 * scale) + _MARGIN
        fy_bot = round((px_h - y_bot) * scale)
        fy_top = round((px_h - y_top) * scale)
        if fx1 > fx0 and fy_top > fy_bot:
            font_rects.append((fx0, fy_bot, fx1, fy_top))

    advance_width = max(1, round(px_w * scale) + 2 * _MARGIN)
    return font_rects, advance_width


def _draw_rects_ttf(pen: TTGlyphPen, rects: list[tuple[int, int, int, int]]) -> None:
    """Draw font-unit rects as TrueType contours."""
    for x0, y0, x1, y1 in rects:
        pen.moveTo((x0, y0))
        pen.lineTo((x0, y1))
        pen.lineTo((x1, y1))
        pen.lineTo((x1, y0))
        pen.closePath()


def _draw_rects_cff(pen: T2CharStringPen, rects: list[tuple[int, int, int, int]]) -> None:
    """Draw font-unit rects as CFF T2 contours."""
    for x0, y0, x1, y1 in rects:
        pen.moveTo((x0, y0))
        pen.lineTo((x0, y1))
        pen.lineTo((x1, y1))
        pen.lineTo((x1, y0))
        pen.closePath()


def _load_font_rects(
    glyph: Glyph,
    glyph_dir: str,
) -> tuple[list[tuple[int, int, int, int]], int]:
    """Return font-unit rects and advance width for *glyph*.

    Falls back to the .notdef outline when the crop file is missing or
    produces no foreground pixels.
    """
    crop_path = os.path.join(glyph_dir, glyph.filename)
    if os.path.exists(crop_path):
        pixel_rects, px_w, px_h = get_glyph_rects(crop_path)
        if pixel_rects:
            return _pixel_rects_to_font_rects(pixel_rects, px_w, px_h)

    notdef_adv = _CAP_HEIGHT // 2 + _MARGIN * 2
    return _notdef_rects(), notdef_adv


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def export_font(
    font_name: str,
    style_name: str,
    glyphs: list[Glyph],
    glyph_dir: str,
    format: FontFormat = "ttf",
) -> bytes:
    """Build a font file from *glyphs* and return its raw bytes.

    Only glyphs with a single-character ``label`` are embedded; unlabelled
    glyphs are silently skipped.  When duplicate labels exist, only the
    first occurrence is used.

    Parameters
    ----------
    font_name:
        Font family name written into the ``name`` table.
    style_name:
        Style name (e.g. ``"Regular"``).
    glyphs:
        Collection of :class:`~app.models.Glyph` objects to include.
    glyph_dir:
        Directory containing the glyph crop PNG files.
    format:
        ``"ttf"`` for TrueType or ``"otf"`` for OpenType/CFF.

    Returns
    -------
    Binary font file contents.
    """
    is_ttf = format.lower() == "ttf"

    # Collect unique single-char labelled glyphs, sorted by code point
    seen: set[str] = set()
    labelled: list[tuple[int, str, Glyph]] = []
    for g in glyphs:
        if g.label and len(g.label) == 1 and g.label not in seen:
            labelled.append((ord(g.label), g.label, g))
            seen.add(g.label)
    labelled.sort(key=lambda t: t[0])

    glyph_order = [".notdef"] + [lbl for _, lbl, _ in labelled]
    cmap: dict[int, str] = {cp: lbl for cp, lbl, _ in labelled}

    fb = FontBuilder(_UNITS_PER_EM, isTTF=is_ttf)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)

    notdef_adv = _CAP_HEIGHT // 2 + _MARGIN * 2
    metrics: dict[str, tuple[int, int]] = {".notdef": (notdef_adv, _MARGIN)}

    if is_ttf:
        ttf_glyphs: dict[str, object] = {}

        pen = TTGlyphPen(None)
        _draw_rects_ttf(pen, _notdef_rects())
        ttf_glyphs[".notdef"] = pen.glyph()

        for _, label, glyph in labelled:
            rects, adv = _load_font_rects(glyph, glyph_dir)
            pen = TTGlyphPen(None)
            _draw_rects_ttf(pen, rects)
            ttf_glyphs[label] = pen.glyph()
            metrics[label] = (adv, _MARGIN)

        fb.setupGlyf(ttf_glyphs)

    else:
        charstrings: dict[str, object] = {}

        pen = T2CharStringPen(notdef_adv, None)
        _draw_rects_cff(pen, _notdef_rects())
        charstrings[".notdef"] = pen.getCharString()

        for _, label, glyph in labelled:
            rects, adv = _load_font_rects(glyph, glyph_dir)
            pen = T2CharStringPen(adv, None)
            _draw_rects_cff(pen, rects)
            charstrings[label] = pen.getCharString()
            metrics[label] = (adv, _MARGIN)

        ps_name = f"{font_name.replace(' ', '')}-{style_name.replace(' ', '')}"
        fb.setupCFF(
            ps_name,
            {"FullName": f"{font_name} {style_name}", "version": "1.0"},
            charstrings,
            {},
        )

    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=_ASCENT, descent=_DESCENT)
    fb.setupNameTable({"familyName": font_name, "styleName": style_name})
    fb.setupOS2(
        sTypoAscender=_ASCENT,
        sTypoDescender=_DESCENT,
        sTypoLineGap=0,
        usWinAscent=_ASCENT,
        usWinDescent=abs(_DESCENT),
    )
    fb.setupPost()
    fb.setupHead(unitsPerEm=_UNITS_PER_EM)

    buf = io.BytesIO()
    fb.font.save(buf)
    return buf.getvalue()
