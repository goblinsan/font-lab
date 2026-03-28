"""Missing glyph reconstruction.

For a font sample with a partial set of labelled glyphs, this module
synthesises crops for any characters absent from the target charset.
Existing character shapes are reused where a visually similar donor can
be found; otherwise a blank placeholder crop with average dimensions is
created.
"""

from __future__ import annotations

import os
import shutil
import string
import uuid

from PIL import Image

from app.models import Glyph

# ---------------------------------------------------------------------------
# Character similarity mapping
# Used to find a visually close donor glyph when a character is missing.
# ---------------------------------------------------------------------------

_SIMILAR: dict[str, str] = {
    # Lowercase
    "a": "o",
    "b": "d",
    "c": "o",
    "d": "b",
    "e": "c",
    "g": "o",
    "m": "n",
    "n": "m",
    "p": "b",
    "q": "p",
    "u": "n",
    "v": "u",
    # Uppercase
    "B": "D",
    "C": "G",
    "D": "O",
    "G": "C",
    "O": "D",
    "P": "F",
    "Q": "O",
    "R": "P",
    # Digit lookalikes
    "0": "O",
    "1": "I",
    "5": "S",
    "6": "G",
    "8": "B",
}

DEFAULT_CHARSET: str = string.ascii_letters + string.digits


def reconstruct_missing_glyphs(
    sample_id: int,
    existing_glyphs: list[Glyph],
    glyph_dir: str,
    charset: str = DEFAULT_CHARSET,
) -> list[Glyph]:
    """Synthesise glyph crops for characters absent from *existing_glyphs*.

    Algorithm
    ---------
    1. Build a ``{label: Glyph}`` map from glyphs that already have a label.
    2. For each character *c* in *charset* that has no entry:

       a. Look up a similar donor character in :data:`_SIMILAR`.
       b. If a donor glyph exists on disk, copy its crop to a new file.
       c. Otherwise create a blank (white) crop whose dimensions match the
          average of all existing glyphs.

    3. Return a list of newly-created :class:`~app.models.Glyph` objects.
       The caller is responsible for adding them to the DB and committing.

    Parameters
    ----------
    sample_id:
        The ``FontSample`` ID this reconstruction belongs to.
    existing_glyphs:
        All ``Glyph`` objects already associated with *sample_id*.
    glyph_dir:
        Directory where glyph crop images live.
    charset:
        Target set of characters that should be present after reconstruction.
    """
    os.makedirs(glyph_dir, exist_ok=True)

    labelled: dict[str, Glyph] = {
        g.label: g for g in existing_glyphs if g.label is not None
    }

    # Average glyph dimensions — used as fallback for blank placeholders
    if existing_glyphs:
        total_w = sum(g.bbox_w for g in existing_glyphs)
        total_h = sum(g.bbox_h for g in existing_glyphs)
        count = len(existing_glyphs)
        avg_w = max(1, round(total_w / count))
        avg_h = max(1, round(total_h / count))
    else:
        avg_w, avg_h = 30, 40

    new_glyphs: list[Glyph] = []

    for char in charset:
        if char in labelled:
            continue  # Already present — nothing to synthesise

        donor_glyph: Glyph | None = None
        donor_char = _SIMILAR.get(char)
        if donor_char and donor_char in labelled:
            donor_glyph = labelled[donor_char]

        filename = f"{uuid.uuid4().hex}.png"
        dest_path = os.path.join(glyph_dir, filename)

        if donor_glyph is not None:
            src_path = os.path.join(glyph_dir, donor_glyph.filename)
            if os.path.exists(src_path):
                shutil.copy2(src_path, dest_path)
                bbox_w, bbox_h = donor_glyph.bbox_w, donor_glyph.bbox_h
            else:
                donor_glyph = None  # File missing — fall back to blank

        if donor_glyph is None:
            img = Image.new("L", (avg_w, avg_h), color=255)
            img.save(dest_path)
            bbox_w, bbox_h = avg_w, avg_h

        new_glyphs.append(
            Glyph(
                sample_id=sample_id,
                filename=filename,
                bbox_x=0,
                bbox_y=0,
                bbox_w=bbox_w,
                bbox_h=bbox_h,
                label=char,
                verified=False,
                synthesized=True,
            )
        )

    return new_glyphs
