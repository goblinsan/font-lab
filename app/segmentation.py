"""Glyph segmentation utilities.

Uses a projection-histogram approach (row then column sweeps) to locate
individual character bounding boxes inside a greyscale font-sample image.
Only Pillow is required — no numpy or OpenCV dependency.
"""

from __future__ import annotations

import os
import uuid
from typing import TypedDict

from PIL import Image, ImageOps


class GlyphInfo(TypedDict):
    filename: str
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _otsu_threshold(histogram: list[int], total_pixels: int) -> int:
    """Compute Otsu's threshold from a 256-bucket greyscale histogram."""
    best_t = 0
    best_var = 0.0

    cumulative_count = 0
    cumulative_sum = 0

    for t in range(256):
        cumulative_count += histogram[t]
        cumulative_sum += t * histogram[t]

    total_sum = cumulative_sum
    bg_count = 0
    bg_sum = 0

    for t in range(256):
        bg_count += histogram[t]
        bg_sum += t * histogram[t]
        if bg_count == 0 or bg_count == total_pixels:
            continue
        fg_count = total_pixels - bg_count
        bg_mean = bg_sum / bg_count
        fg_mean = (total_sum - bg_sum) / fg_count
        between_var = bg_count * fg_count * (bg_mean - fg_mean) ** 2
        if between_var > best_var:
            best_var = between_var
            best_t = t

    return best_t


def _find_runs(histogram: list[int], min_gap: int = 1) -> list[tuple[int, int]]:
    """Return (start, end) index pairs for non-zero runs in *histogram*.

    Consecutive zero buckets of length < *min_gap* are treated as part of the
    same run (allows small inter-pixel gaps inside a glyph).
    """
    runs: list[tuple[int, int]] = []
    n = len(histogram)
    i = 0
    while i < n:
        if histogram[i] > 0:
            start = i
            end = i
            while i < n:
                if histogram[i] > 0:
                    end = i
                    i += 1
                else:
                    # Look ahead for min_gap
                    gap = 0
                    j = i
                    while j < n and histogram[j] == 0:
                        gap += 1
                        j += 1
                    if gap < min_gap or j == n:
                        # Gap is within tolerance – keep going
                        i = j
                    else:
                        break
            runs.append((start, end))
        else:
            i += 1
    return runs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def segment_glyphs(
    image_path: str,
    output_dir: str,
    *,
    min_glyph_w: int = 4,
    min_glyph_h: int = 4,
    padding: int = 2,
    intra_glyph_gap: int = 2,
) -> list[GlyphInfo]:
    """Extract individual glyph crops from *image_path* and save them to *output_dir*.

    Algorithm
    ---------
    1. Convert image to greyscale and apply Otsu's binarisation.
    2. Invert so that glyph pixels are white (foreground = 1).
    3. Build a row-projection histogram; segment it into text *lines*.
    4. For each line, build a column-projection histogram; segment it into
       individual *character* columns.
    5. Crop, add padding, and save each character crop as a PNG.

    Parameters
    ----------
    image_path:
        Path to the source font-sample image.
    output_dir:
        Directory in which glyph PNG crops are written.
    min_glyph_w, min_glyph_h:
        Minimum pixel dimensions; smaller regions are treated as noise.
    padding:
        Extra pixels added around each crop (clamped to image bounds).
    intra_glyph_gap:
        How many consecutive empty rows/columns may appear *inside* a glyph
        before it is split into two separate glyphs.

    Returns
    -------
    List of :class:`GlyphInfo` dicts describing each extracted crop.
    """
    os.makedirs(output_dir, exist_ok=True)

    img = Image.open(image_path).convert("L")
    width, height = img.size

    # Build greyscale histogram and compute Otsu threshold
    hist = img.histogram()  # 256 buckets
    threshold = _otsu_threshold(hist, width * height)

    # Binarise: foreground (glyph) pixels become 255, background 0
    binary = img.point(lambda p: 255 if p <= threshold else 0)

    pixels = binary.load()

    # Row projection: count foreground pixels per row
    row_proj = [
        sum(1 for x in range(width) if pixels[x, y] == 255)  # type: ignore[index]
        for y in range(height)
    ]

    line_runs = _find_runs(row_proj, min_gap=intra_glyph_gap)

    results: list[GlyphInfo] = []

    for line_y0, line_y1 in line_runs:
        if line_y1 - line_y0 < min_glyph_h:
            continue

        # Column projection within this line band
        col_proj = [
            sum(1 for y in range(line_y0, line_y1 + 1) if pixels[x, y] == 255)  # type: ignore[index]
            for x in range(width)
        ]

        char_runs = _find_runs(col_proj, min_gap=intra_glyph_gap)

        for char_x0, char_x1 in char_runs:
            if char_x1 - char_x0 < min_glyph_w:
                continue

            # Tight vertical bounds within this column range
            row_proj_col = [
                sum(1 for x in range(char_x0, char_x1 + 1) if pixels[x, y] == 255)  # type: ignore[index]
                for y in range(line_y0, line_y1 + 1)
            ]
            tight_rows = [
                line_y0 + i for i, v in enumerate(row_proj_col) if v > 0
            ]
            if not tight_rows:
                continue
            char_y0 = tight_rows[0]
            char_y1 = tight_rows[-1]
            if char_y1 - char_y0 < min_glyph_h:
                continue

            # Apply padding (clamped)
            crop_x0 = max(0, char_x0 - padding)
            crop_y0 = max(0, char_y0 - padding)
            crop_x1 = min(width - 1, char_x1 + padding)
            crop_y1 = min(height - 1, char_y1 + padding)

            crop = img.crop((crop_x0, crop_y0, crop_x1 + 1, crop_y1 + 1))

            filename = f"{uuid.uuid4().hex}.png"
            crop.save(os.path.join(output_dir, filename))

            results.append(
                GlyphInfo(
                    filename=filename,
                    bbox_x=crop_x0,
                    bbox_y=crop_y0,
                    bbox_w=crop_x1 - crop_x0 + 1,
                    bbox_h=crop_y1 - crop_y0 + 1,
                )
            )

    return results
