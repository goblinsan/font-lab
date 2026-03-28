"""Glyph vectorization: convert a raster crop to SVG path data.

Uses a scanline approach — each row of foreground pixels produces one or
more axis-aligned filled rectangles.  Only Pillow is required; no NumPy
or OpenCV dependency.
"""

from __future__ import annotations

from PIL import Image

from app.segmentation import _otsu_threshold


def get_glyph_rects(image_path: str) -> tuple[list[tuple[int, int, int, int]], int, int]:
    """Return the foreground pixel spans of a glyph crop as rectangles.

    Parameters
    ----------
    image_path:
        Path to the glyph crop image.

    Returns
    -------
    ``(rects, width_px, height_px)`` where each rect is
    ``(x0, y, x1, y + 1)`` — the left column (inclusive), the row index
    (from the top), the right column (exclusive), and the bottom row
    (exclusive).  All values are in pixel coordinates (y increases
    downward).
    """
    img = Image.open(image_path).convert("L")
    w, h = img.size

    hist = img.histogram()
    threshold = _otsu_threshold(hist, w * h)
    binary = img.point(lambda p: 255 if p <= threshold else 0)
    pixels = binary.load()

    rects: list[tuple[int, int, int, int]] = []
    for y in range(h):
        in_run = False
        x_start = 0
        for x in range(w):
            if pixels[x, y] == 255:  # type: ignore[index]
                if not in_run:
                    x_start = x
                    in_run = True
            else:
                if in_run:
                    rects.append((x_start, y, x, y + 1))
                    in_run = False
        if in_run:
            rects.append((x_start, y, w, y + 1))

    return rects, w, h


def glyph_to_svg(image_path: str) -> str:
    """Return a complete SVG document for the glyph at *image_path*.

    The SVG uses the image's pixel dimensions as the ``viewBox`` so it
    scales without distortion.
    """
    rects, w, h = get_glyph_rects(image_path)
    parts = [f"M {x0} {y0} H {x1} V {y1} H {x0} Z" for x0, y0, x1, y1 in rects]
    path_data = " ".join(parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">'
        f'<path fill="#000000" d="{path_data}"/>'
        f"</svg>"
    )
