"""Tests for the editor and QA tool endpoints (Issues #19, #20, #21)."""

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
# Issue #19 — GET /api/samples/{id}/compare
# ---------------------------------------------------------------------------

class TestCompareView:
    def test_compare_sample_not_found(self, client):
        resp = client.get("/api/samples/99999/compare")
        assert resp.status_code == 404

    def test_compare_empty_when_no_glyphs(self, client):
        resp = client.post(
            "/api/samples/",
            files={"file": ("s.png", io.BytesIO(make_segmentable_image_bytes()), "image/png")},
            data={"font_name": "EmptyFont"},
        )
        sample = resp.json()
        cmp_resp = client.get(f"/api/samples/{sample['id']}/compare")
        assert cmp_resp.status_code == 200
        assert cmp_resp.json() == []

    def test_compare_returns_list_after_segment(self, client):
        sample, glyphs = _upload_and_segment(client)
        resp = client.get(f"/api/samples/{sample['id']}/compare")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == len(glyphs)

    def test_compare_entry_fields(self, client):
        sample, glyphs = _upload_and_segment(client)
        resp = client.get(f"/api/samples/{sample['id']}/compare")
        assert resp.status_code == 200
        entry = resp.json()[0]
        for field in ("id", "label", "source_url", "outline_url", "verified", "synthesized"):
            assert field in entry, f"Missing field: {field}"

    def test_compare_urls_are_correct(self, client):
        sample, glyphs = _upload_and_segment(client)
        resp = client.get(f"/api/samples/{sample['id']}/compare")
        assert resp.status_code == 200
        entry = resp.json()[0]
        glyph_id = entry["id"]
        assert entry["source_url"].startswith("/uploads/glyphs/")
        assert entry["outline_url"] == f"/api/glyphs/{glyph_id}/outline"

    def test_compare_reflects_label_and_verified(self, client):
        sample, glyphs = _upload_and_segment(client)
        gid = glyphs[0]["id"]
        client.patch(f"/api/glyphs/{gid}", json={"label": "A", "verified": True})
        resp = client.get(f"/api/samples/{sample['id']}/compare")
        entries = {e["id"]: e for e in resp.json()}
        assert entries[gid]["label"] == "A"
        assert entries[gid]["verified"] is True


# ---------------------------------------------------------------------------
# Issue #20 — Glyph editor: advance_width and left_bearing fields
# ---------------------------------------------------------------------------

class TestGlyphEditorSpacing:
    def test_glyph_response_has_spacing_fields(self, client):
        sample, glyphs = _upload_and_segment(client)
        resp = client.get(f"/api/glyphs/{glyphs[0]['id']}")
        assert resp.status_code == 200
        body = resp.json()
        assert "advance_width" in body
        assert "left_bearing" in body

    def test_update_advance_width(self, client):
        sample, glyphs = _upload_and_segment(client)
        gid = glyphs[0]["id"]
        resp = client.patch(f"/api/glyphs/{gid}", json={"advance_width": 120})
        assert resp.status_code == 200
        assert resp.json()["advance_width"] == 120

    def test_update_left_bearing(self, client):
        sample, glyphs = _upload_and_segment(client)
        gid = glyphs[0]["id"]
        resp = client.patch(f"/api/glyphs/{gid}", json={"left_bearing": 8})
        assert resp.status_code == 200
        assert resp.json()["left_bearing"] == 8

    def test_update_spacing_combined(self, client):
        sample, glyphs = _upload_and_segment(client)
        gid = glyphs[0]["id"]
        resp = client.patch(
            f"/api/glyphs/{gid}",
            json={"advance_width": 200, "left_bearing": 15},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["advance_width"] == 200
        assert body["left_bearing"] == 15

    def test_spacing_defaults_to_none(self, client):
        sample, glyphs = _upload_and_segment(client)
        gid = glyphs[0]["id"]
        resp = client.get(f"/api/glyphs/{gid}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["advance_width"] is None
        assert body["left_bearing"] is None

    def test_spacing_not_overwritten_by_unrelated_patch(self, client):
        """Patching label should leave spacing fields unchanged."""
        sample, glyphs = _upload_and_segment(client)
        gid = glyphs[0]["id"]
        client.patch(f"/api/glyphs/{gid}", json={"advance_width": 100})
        resp = client.patch(f"/api/glyphs/{gid}", json={"label": "X"})
        assert resp.status_code == 200
        assert resp.json()["advance_width"] == 100

    def test_segment_response_includes_spacing_fields(self, client):
        sample, glyphs = _upload_and_segment(client)
        for g in glyphs:
            assert "advance_width" in g
            assert "left_bearing" in g

    def test_glyph_not_found_spacing_patch(self, client):
        resp = client.patch("/api/glyphs/99999", json={"advance_width": 50})
        assert resp.status_code == 404

    def test_advance_width_can_be_set_to_zero(self, client):
        """Ensure advance_width=0 is accepted (not treated as falsy/unset)."""
        sample, glyphs = _upload_and_segment(client)
        gid = glyphs[0]["id"]
        resp = client.patch(f"/api/glyphs/{gid}", json={"advance_width": 0})
        assert resp.status_code == 200
        assert resp.json()["advance_width"] == 0


# ---------------------------------------------------------------------------
# Issue #21 — GET /api/samples/{id}/print-preview
# ---------------------------------------------------------------------------

class TestPrintPreview:
    def test_print_preview_sample_not_found(self, client):
        resp = client.get("/api/samples/99999/print-preview")
        assert resp.status_code == 404

    def test_print_preview_returns_html(self, client):
        sample, glyphs = _upload_and_segment(client)
        resp = client.get(f"/api/samples/{sample['id']}/print-preview")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_print_preview_contains_font_name(self, client):
        sample, glyphs = _upload_and_segment(client)
        resp = client.get(f"/api/samples/{sample['id']}/print-preview")
        assert resp.status_code == 200
        assert "TestFont" in resp.text

    def test_print_preview_contains_preview_sections(self, client):
        sample, _ = _upload_and_segment(client)
        resp = client.get(f"/api/samples/{sample['id']}/print-preview")
        assert resp.status_code == 200
        html = resp.text
        assert "White background" in html
        assert "Dark background" in html
        assert "Kraft background" in html

    def test_print_preview_custom_text(self, client):
        sample, glyphs = _upload_and_segment(client)
        client.patch(f"/api/glyphs/{glyphs[0]['id']}", json={"label": "H"})
        resp = client.get(
            f"/api/samples/{sample['id']}/print-preview",
            params={"text": "Hello"},
        )
        assert resp.status_code == 200
        assert "Hello" in resp.text

    def test_print_preview_uses_labelled_glyphs(self, client):
        sample, glyphs = _upload_and_segment(client)
        client.patch(f"/api/glyphs/{glyphs[0]['id']}", json={"label": "A"})
        resp = client.get(
            f"/api/samples/{sample['id']}/print-preview",
            params={"text": "A"},
        )
        assert resp.status_code == 200
        # The glyph image path should appear in the HTML
        glyph_filename = glyphs[0]["filename"]
        assert glyph_filename in resp.text

    def test_print_preview_custom_font_size(self, client):
        sample, _ = _upload_and_segment(client)
        resp = client.get(
            f"/api/samples/{sample['id']}/print-preview",
            params={"font_size": 72},
        )
        assert resp.status_code == 200
        assert "72px" in resp.text

    def test_print_preview_font_size_bounds(self, client):
        sample, _ = _upload_and_segment(client)
        # Too small
        resp = client.get(
            f"/api/samples/{sample['id']}/print-preview",
            params={"font_size": 2},
        )
        assert resp.status_code == 422
        # Too large
        resp = client.get(
            f"/api/samples/{sample['id']}/print-preview",
            params={"font_size": 999},
        )
        assert resp.status_code == 422

    def test_print_preview_space_characters(self, client):
        sample, _ = _upload_and_segment(client)
        resp = client.get(
            f"/api/samples/{sample['id']}/print-preview",
            params={"text": "A B"},
        )
        assert resp.status_code == 200
        assert "sp-space" in resp.text

    def test_print_preview_missing_chars_are_placeholders(self, client):
        sample, glyphs = _upload_and_segment(client)
        # No glyphs labelled — every character in the text is missing
        resp = client.get(
            f"/api/samples/{sample['id']}/print-preview",
            params={"text": "Z"},
        )
        assert resp.status_code == 200
        assert "sp-missing" in resp.text
