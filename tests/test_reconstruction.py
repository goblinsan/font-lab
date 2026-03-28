"""Tests for the font reconstruction engine.

Covers:
  - GET  /api/glyphs/{id}/outline      — SVG vector outline
  - POST /api/samples/{id}/reconstruct — synthesise missing glyphs
  - POST /api/samples/{id}/export      — export OTF/TTF font file
"""

import io

import pytest

from tests.conftest import make_segmentable_image_bytes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _upload_and_segment(client) -> tuple[dict, list[dict]]:
    """Upload a segmentable sample, run segmentation, return (sample, glyphs)."""
    resp = client.post(
        "/api/samples/",
        files={"file": ("sample.png", io.BytesIO(make_segmentable_image_bytes()), "image/png")},
        data={"font_name": "TestFont"},
    )
    assert resp.status_code == 201
    sample = resp.json()
    glyphs_resp = client.post(f"/api/samples/{sample['id']}/segment")
    assert glyphs_resp.status_code == 201
    return sample, glyphs_resp.json()


# ---------------------------------------------------------------------------
# GET /api/glyphs/{id}/outline
# ---------------------------------------------------------------------------

class TestGlyphOutline:
    def test_outline_returns_svg(self, client):
        sample, glyphs = _upload_and_segment(client)
        gid = glyphs[0]["id"]
        resp = client.get(f"/api/glyphs/{gid}/outline")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("image/svg+xml")
        body = resp.text
        assert "<svg" in body
        assert "</svg>" in body

    def test_outline_contains_path(self, client):
        sample, glyphs = _upload_and_segment(client)
        gid = glyphs[0]["id"]
        resp = client.get(f"/api/glyphs/{gid}/outline")
        assert resp.status_code == 200
        # A real glyph crop should have at least one path segment
        assert '<path' in resp.text

    def test_outline_glyph_not_found(self, client):
        resp = client.get("/api/glyphs/99999/outline")
        assert resp.status_code == 404

    def test_outline_viewbox_matches_glyph_dimensions(self, client):
        sample, glyphs = _upload_and_segment(client)
        g = glyphs[0]
        resp = client.get(f"/api/glyphs/{g['id']}/outline")
        assert resp.status_code == 200
        # viewBox="0 0 <width> <height>" should match the glyph bbox dimensions
        assert f"viewBox=\"0 0 {g['bbox_w']} {g['bbox_h']}\"" in resp.text


# ---------------------------------------------------------------------------
# POST /api/samples/{id}/reconstruct
# ---------------------------------------------------------------------------

class TestReconstruct:
    def test_reconstruct_returns_synthesised_glyphs(self, client):
        sample, glyphs = _upload_and_segment(client)
        # Label one of the two glyphs so reconstruction has a donor
        client.patch(f"/api/glyphs/{glyphs[0]['id']}", json={"label": "A"})
        resp = client.post(
            f"/api/samples/{sample['id']}/reconstruct",
            json={"charset": "AB"},
        )
        assert resp.status_code == 201
        data = resp.json()
        # "A" already exists, so only "B" should be synthesised
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["label"] == "B"
        assert data[0]["synthesized"] is True

    def test_reconstruct_synthesised_flag(self, client):
        sample, glyphs = _upload_and_segment(client)
        resp = client.post(
            f"/api/samples/{sample['id']}/reconstruct",
            json={"charset": "XY"},
        )
        assert resp.status_code == 201
        for g in resp.json():
            assert g["synthesized"] is True
            assert g["verified"] is False

    def test_reconstruct_empty_charset_returns_nothing(self, client):
        sample, _ = _upload_and_segment(client)
        resp = client.post(
            f"/api/samples/{sample['id']}/reconstruct",
            json={"charset": ""},
        )
        assert resp.status_code == 201
        assert resp.json() == []

    def test_reconstruct_all_chars_present_returns_nothing(self, client):
        sample, glyphs = _upload_and_segment(client)
        client.patch(f"/api/glyphs/{glyphs[0]['id']}", json={"label": "A"})
        resp = client.post(
            f"/api/samples/{sample['id']}/reconstruct",
            json={"charset": "A"},
        )
        assert resp.status_code == 201
        assert resp.json() == []

    def test_reconstruct_reruns_replace_synthesised(self, client):
        sample, _ = _upload_and_segment(client)
        first = client.post(
            f"/api/samples/{sample['id']}/reconstruct",
            json={"charset": "PQ"},
        ).json()
        assert len(first) == 2

        second = client.post(
            f"/api/samples/{sample['id']}/reconstruct",
            json={"charset": "PQ"},
        ).json()
        # Re-running should still yield exactly 2 synthesised glyphs — not doubled
        assert len(second) == 2
        # The full glyph list should reflect only the current run (2 original + 2 synthesised)
        total = client.get(f"/api/samples/{sample['id']}/glyphs").json()
        assert len(total) == 4

    def test_reconstruct_sample_not_found(self, client):
        resp = client.post("/api/samples/99999/reconstruct", json={})
        assert resp.status_code == 404

    def test_reconstruct_uses_donor_similarity(self, client):
        """When 'O' is labelled, reconstructing 'Q' should use it as a donor."""
        sample, glyphs = _upload_and_segment(client)
        client.patch(f"/api/glyphs/{glyphs[0]['id']}", json={"label": "O"})
        resp = client.post(
            f"/api/samples/{sample['id']}/reconstruct",
            json={"charset": "Q"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert len(data) == 1
        assert data[0]["label"] == "Q"
        assert data[0]["synthesized"] is True
        # Donor glyph dimensions should be copied
        donor_w = glyphs[0]["bbox_w"]
        donor_h = glyphs[0]["bbox_h"]
        assert data[0]["bbox_w"] == donor_w
        assert data[0]["bbox_h"] == donor_h

    def test_reconstruct_glyph_fields(self, client):
        sample, _ = _upload_and_segment(client)
        resp = client.post(
            f"/api/samples/{sample['id']}/reconstruct",
            json={"charset": "Z"},
        )
        assert resp.status_code == 201
        g = resp.json()[0]
        for field in ("id", "sample_id", "filename", "bbox_x", "bbox_y", "bbox_w", "bbox_h", "synthesized"):
            assert field in g, f"Missing field: {field}"
        assert g["sample_id"] == sample["id"]


# ---------------------------------------------------------------------------
# POST /api/samples/{id}/export
# ---------------------------------------------------------------------------

class TestExport:
    def _prepare_labelled_sample(self, client):
        """Upload, segment and label both glyphs, then return the sample."""
        sample, glyphs = _upload_and_segment(client)
        client.patch(f"/api/glyphs/{glyphs[0]['id']}", json={"label": "A"})
        client.patch(f"/api/glyphs/{glyphs[1]['id']}", json={"label": "B"})
        return sample

    def test_export_ttf_returns_bytes(self, client):
        sample = self._prepare_labelled_sample(client)
        resp = client.post(
            f"/api/samples/{sample['id']}/export",
            json={"format": "ttf"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "font/ttf"
        assert len(resp.content) > 0

    def test_export_otf_returns_bytes(self, client):
        sample = self._prepare_labelled_sample(client)
        resp = client.post(
            f"/api/samples/{sample['id']}/export",
            json={"format": "otf"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "font/otf"
        assert len(resp.content) > 0

    def test_export_ttf_is_valid_font(self, client):
        """Verify the returned TTF can be loaded by fontTools."""
        from fontTools.ttLib import TTFont
        import io as _io

        sample = self._prepare_labelled_sample(client)
        resp = client.post(
            f"/api/samples/{sample['id']}/export",
            json={"format": "ttf"},
        )
        assert resp.status_code == 200
        font = TTFont(_io.BytesIO(resp.content))
        assert "glyf" in font
        assert "cmap" in font
        cmap = font.getBestCmap()
        assert ord("A") in cmap
        assert ord("B") in cmap

    def test_export_otf_is_valid_font(self, client):
        """Verify the returned OTF can be loaded by fontTools."""
        from fontTools.ttLib import TTFont
        import io as _io

        sample = self._prepare_labelled_sample(client)
        resp = client.post(
            f"/api/samples/{sample['id']}/export",
            json={"format": "otf"},
        )
        assert resp.status_code == 200
        font = TTFont(_io.BytesIO(resp.content))
        assert "CFF " in font
        assert "cmap" in font
        cmap = font.getBestCmap()
        assert ord("A") in cmap
        assert ord("B") in cmap

    def test_export_content_disposition_header(self, client):
        sample = self._prepare_labelled_sample(client)
        resp = client.post(
            f"/api/samples/{sample['id']}/export",
            json={"format": "ttf", "font_name": "MyFont"},
        )
        assert resp.status_code == 200
        cd = resp.headers.get("content-disposition", "")
        assert "attachment" in cd
        assert ".ttf" in cd

    def test_export_default_ttf(self, client):
        """Omitting format should default to TTF."""
        sample = self._prepare_labelled_sample(client)
        resp = client.post(f"/api/samples/{sample['id']}/export", json={})
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "font/ttf"

    def test_export_invalid_format(self, client):
        sample, _ = _upload_and_segment(client)
        resp = client.post(
            f"/api/samples/{sample['id']}/export",
            json={"format": "woff"},
        )
        assert resp.status_code == 400

    def test_export_no_labelled_glyphs_still_produces_font(self, client):
        """A sample with no labelled glyphs should still yield a minimal font."""
        from fontTools.ttLib import TTFont
        import io as _io

        sample, _ = _upload_and_segment(client)
        resp = client.post(
            f"/api/samples/{sample['id']}/export",
            json={"format": "ttf"},
        )
        assert resp.status_code == 200
        font = TTFont(_io.BytesIO(resp.content))
        assert ".notdef" in font.getGlyphOrder()

    def test_export_sample_not_found(self, client):
        resp = client.post("/api/samples/99999/export", json={})
        assert resp.status_code == 404
