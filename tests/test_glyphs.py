"""Tests for the glyph segmentation and correction API."""

import io

import pytest

from tests.conftest import make_image_bytes, make_segmentable_image_bytes, make_blank_image_bytes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _upload_sample(client, image_bytes: bytes | None = None, font_name: str = "TestFont"):
    """Upload a font sample and return the parsed JSON response."""
    data = make_image_bytes() if image_bytes is None else image_bytes
    resp = client.post(
        "/api/samples/",
        files={"file": ("sample.png", io.BytesIO(data), "image/png")},
        data={"font_name": font_name},
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Segmentation trigger (POST /api/samples/{id}/segment)
# ---------------------------------------------------------------------------

class TestSegment:
    def test_segment_sample_not_found(self, client):
        resp = client.post("/api/samples/99999/segment")
        assert resp.status_code == 404

    def test_segment_returns_list(self, client):
        sample = _upload_sample(client, make_segmentable_image_bytes())
        resp = client.post(f"/api/samples/{sample['id']}/segment")
        assert resp.status_code == 201
        glyphs = resp.json()
        assert isinstance(glyphs, list)
        # Our synthetic image has two distinct dark rectangles
        assert len(glyphs) == 2

    def test_segment_glyph_fields(self, client):
        sample = _upload_sample(client, make_segmentable_image_bytes())
        resp = client.post(f"/api/samples/{sample['id']}/segment")
        assert resp.status_code == 201
        glyph = resp.json()[0]
        for field in ("id", "sample_id", "filename", "bbox_x", "bbox_y", "bbox_w", "bbox_h"):
            assert field in glyph, f"Missing field: {field}"
        assert glyph["sample_id"] == sample["id"]
        assert glyph["verified"] is False
        assert glyph["label"] is None
        assert glyph["bbox_w"] > 0
        assert glyph["bbox_h"] > 0

    def test_segment_reruns_replace_glyphs(self, client):
        sample = _upload_sample(client, make_segmentable_image_bytes())
        sid = sample["id"]
        first = client.post(f"/api/samples/{sid}/segment").json()
        second = client.post(f"/api/samples/{sid}/segment").json()
        # After a re-run exactly two fresh glyphs exist
        assert len(second) == 2
        # The list endpoint reflects only the current run
        listed = client.get(f"/api/samples/{sid}/glyphs").json()
        assert {g["id"] for g in listed} == {g["id"] for g in second}

    def test_segment_trivial_image_produces_no_glyphs(self, client):
        # An all-white image should yield no glyph segments
        sample = _upload_sample(client, make_blank_image_bytes())
        resp = client.post(f"/api/samples/{sample['id']}/segment")
        assert resp.status_code == 201
        assert resp.json() == []


# ---------------------------------------------------------------------------
# List glyphs (GET /api/samples/{id}/glyphs)
# ---------------------------------------------------------------------------

class TestListGlyphs:
    def test_list_glyphs_empty(self, client):
        sample = _upload_sample(client)
        resp = client.get(f"/api/samples/{sample['id']}/glyphs")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_glyphs_after_segment(self, client):
        sample = _upload_sample(client, make_segmentable_image_bytes())
        client.post(f"/api/samples/{sample['id']}/segment")
        resp = client.get(f"/api/samples/{sample['id']}/glyphs")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_glyphs_sample_not_found(self, client):
        resp = client.get("/api/samples/99999/glyphs")
        assert resp.status_code == 404

    def test_list_glyphs_ordered_by_position(self, client):
        sample = _upload_sample(client, make_segmentable_image_bytes())
        client.post(f"/api/samples/{sample['id']}/segment")
        glyphs = client.get(f"/api/samples/{sample['id']}/glyphs").json()
        xs = [g["bbox_x"] for g in glyphs]
        assert xs == sorted(xs)


# ---------------------------------------------------------------------------
# Single glyph retrieval (GET /api/glyphs/{id})
# ---------------------------------------------------------------------------

class TestGetGlyph:
    def test_get_existing_glyph(self, client):
        sample = _upload_sample(client, make_segmentable_image_bytes())
        glyphs = client.post(f"/api/samples/{sample['id']}/segment").json()
        glyph_id = glyphs[0]["id"]
        resp = client.get(f"/api/glyphs/{glyph_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == glyph_id

    def test_get_glyph_not_found(self, client):
        resp = client.get("/api/glyphs/99999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Update glyph (PATCH /api/glyphs/{id})
# ---------------------------------------------------------------------------

class TestUpdateGlyph:
    def test_update_label(self, client):
        sample = _upload_sample(client, make_segmentable_image_bytes())
        glyphs = client.post(f"/api/samples/{sample['id']}/segment").json()
        gid = glyphs[0]["id"]
        resp = client.patch(f"/api/glyphs/{gid}", json={"label": "A"})
        assert resp.status_code == 200
        assert resp.json()["label"] == "A"

    def test_update_verified(self, client):
        sample = _upload_sample(client, make_segmentable_image_bytes())
        glyphs = client.post(f"/api/samples/{sample['id']}/segment").json()
        gid = glyphs[0]["id"]
        resp = client.patch(f"/api/glyphs/{gid}", json={"verified": True})
        assert resp.status_code == 200
        assert resp.json()["verified"] is True

    def test_update_bbox(self, client):
        sample = _upload_sample(client, make_segmentable_image_bytes())
        glyphs = client.post(f"/api/samples/{sample['id']}/segment").json()
        gid = glyphs[0]["id"]
        resp = client.patch(f"/api/glyphs/{gid}", json={"bbox_x": 5, "bbox_y": 3, "bbox_w": 10, "bbox_h": 12})
        assert resp.status_code == 200
        body = resp.json()
        assert body["bbox_x"] == 5
        assert body["bbox_y"] == 3
        assert body["bbox_w"] == 10
        assert body["bbox_h"] == 12

    def test_update_glyph_not_found(self, client):
        resp = client.patch("/api/glyphs/99999", json={"label": "Z"})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Delete glyph (DELETE /api/glyphs/{id})
# ---------------------------------------------------------------------------

class TestDeleteGlyph:
    def test_delete_glyph(self, client):
        sample = _upload_sample(client, make_segmentable_image_bytes())
        glyphs = client.post(f"/api/samples/{sample['id']}/segment").json()
        gid = glyphs[0]["id"]
        resp = client.delete(f"/api/glyphs/{gid}")
        assert resp.status_code == 204
        assert client.get(f"/api/glyphs/{gid}").status_code == 404

    def test_delete_glyph_not_found(self, client):
        resp = client.delete("/api/glyphs/99999")
        assert resp.status_code == 404
