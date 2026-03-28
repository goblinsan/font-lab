"""Tests for the v1 versioned REST API (issues #27, #28, #29, #30)."""

import io

from tests.conftest import make_image_bytes


def _upload(client, font_name=None, font_category=None, style=None, theme=None,
            era=None, provenance=None, confidence=None, tags="", notes=None):
    data = {}
    if font_name:
        data["font_name"] = font_name
    if font_category:
        data["font_category"] = font_category
    if style:
        data["style"] = style
    if theme:
        data["theme"] = theme
    if era:
        data["era"] = era
    if provenance:
        data["provenance"] = provenance
    if confidence is not None:
        data["confidence"] = str(confidence)
    if tags:
        data["tags"] = tags
    if notes:
        data["notes"] = notes
    resp = client.post(
        "/api/samples/",
        files={"file": ("f.png", io.BytesIO(make_image_bytes()), "image/png")},
        data=data,
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Issue #28 – Extended metadata fields (era, provenance, confidence)
# ---------------------------------------------------------------------------

class TestExtendedMetadata:
    def test_upload_with_era_and_provenance(self, client):
        sample = _upload(
            client,
            font_name="Windsor",
            era="1920s",
            provenance="European foundry",
        )
        assert sample["era"] == "1920s"
        assert sample["provenance"] == "European foundry"

    def test_upload_with_confidence(self, client):
        sample = _upload(client, font_name="Garamond", confidence=0.85)
        assert sample["confidence"] == 0.85

    def test_update_era_field(self, client):
        sample = _upload(client, font_name="Bodoni")
        resp = client.patch(f"/api/samples/{sample['id']}", json={"era": "1800s"})
        assert resp.status_code == 200
        assert resp.json()["era"] == "1800s"

    def test_update_provenance_field(self, client):
        sample = _upload(client, font_name="Caslon")
        resp = client.patch(f"/api/samples/{sample['id']}", json={"provenance": "UK press"})
        assert resp.status_code == 200
        assert resp.json()["provenance"] == "UK press"

    def test_update_confidence_field(self, client):
        sample = _upload(client, font_name="Univers")
        resp = client.patch(f"/api/samples/{sample['id']}", json={"confidence": 0.95})
        assert resp.status_code == 200
        assert resp.json()["confidence"] == 0.95


# ---------------------------------------------------------------------------
# Issue #27 – GET /api/v1/fonts – paginated list
# ---------------------------------------------------------------------------

class TestV1ListFonts:
    def test_empty_catalog(self, client):
        resp = client.get("/api/v1/fonts")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []
        assert body["page"] == 1

    def test_paginated_response_shape(self, client):
        _upload(client, font_name="Arial")
        resp = client.get("/api/v1/fonts")
        body = resp.json()
        assert "total" in body
        assert "page" in body
        assert "per_page" in body
        assert "items" in body

    def test_pagination_limits_results(self, client):
        for i in range(5):
            _upload(client, font_name=f"Font{i}")
        resp = client.get("/api/v1/fonts?per_page=2&page=1")
        body = resp.json()
        assert body["total"] == 5
        assert len(body["items"]) == 2

    def test_pagination_second_page(self, client):
        for i in range(5):
            _upload(client, font_name=f"Font{i}")
        resp = client.get("/api/v1/fonts?per_page=3&page=2")
        body = resp.json()
        assert body["total"] == 5
        assert len(body["items"]) == 2

    def test_filter_by_style(self, client):
        _upload(client, font_name="Helvetica", style="Sans-Serif")
        _upload(client, font_name="Garamond", style="Serif")
        resp = client.get("/api/v1/fonts?style=Sans-Serif")
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["font_name"] == "Helvetica"

    def test_filter_by_era(self, client):
        _upload(client, font_name="Windsor", era="1920s")
        _upload(client, font_name="Helvetica", era="1950s")
        resp = client.get("/api/v1/fonts?era=1920s")
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["font_name"] == "Windsor"

    def test_sort_by_font_name_asc(self, client):
        _upload(client, font_name="Zig")
        _upload(client, font_name="Alpha")
        resp = client.get("/api/v1/fonts?sort=font_name&order=asc")
        items = resp.json()["items"]
        assert items[0]["font_name"] == "Alpha"
        assert items[1]["font_name"] == "Zig"

    def test_items_include_preview_url(self, client):
        sample = _upload(client, font_name="Futura")
        resp = client.get("/api/v1/fonts")
        item = resp.json()["items"][0]
        assert item["preview_url"] == f"/uploads/{sample['filename']}"

    def test_items_include_glyph_count(self, client):
        _upload(client, font_name="Futura")
        resp = client.get("/api/v1/fonts")
        item = resp.json()["items"][0]
        assert "glyph_count" in item
        assert item["glyph_count"] == 0


# ---------------------------------------------------------------------------
# Issue #27 – GET /api/v1/fonts/search – semantic search with pagination
# ---------------------------------------------------------------------------

class TestV1SearchFonts:
    def test_search_by_era(self, client):
        _upload(client, font_name="Windsor", era="Victorian")
        _upload(client, font_name="Helvetica", era="Modern")
        resp = client.get("/api/v1/fonts/search?era=Victorian")
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["font_name"] == "Windsor"

    def test_search_by_freetext_includes_era(self, client):
        _upload(client, font_name="Windsor", era="Victorian")
        resp = client.get("/api/v1/fonts/search?q=Victorian")
        assert resp.json()["total"] == 1

    def test_search_returns_paginated_shape(self, client):
        _upload(client, font_name="Arial")
        resp = client.get("/api/v1/fonts/search?font_name=Arial")
        body = resp.json()
        assert "total" in body
        assert "page" in body
        assert "per_page" in body
        assert "items" in body

    def test_search_pagination(self, client):
        for i in range(5):
            _upload(client, font_name=f"Futura{i}", style="Sans-Serif")
        resp = client.get("/api/v1/fonts/search?style=Sans-Serif&per_page=2&page=1")
        body = resp.json()
        assert body["total"] == 5
        assert len(body["items"]) == 2

    def test_search_no_results(self, client):
        resp = client.get("/api/v1/fonts/search?q=NonExistentXYZ123")
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []


# ---------------------------------------------------------------------------
# Issue #27 – GET /api/v1/fonts/{id}
# ---------------------------------------------------------------------------

class TestV1GetFont:
    def test_get_existing_font(self, client):
        sample = _upload(client, font_name="Optima", style="Humanist", era="1950s")
        resp = client.get(f"/api/v1/fonts/{sample['id']}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["font_name"] == "Optima"
        assert body["style"] == "Humanist"
        assert body["era"] == "1950s"
        assert "preview_url" in body

    def test_get_missing_font_returns_404(self, client):
        resp = client.get("/api/v1/fonts/99999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Issue #29 – GET /api/v1/fonts/{id}/similar – similarity ranking
# ---------------------------------------------------------------------------

class TestV1SimilarFonts:
    def test_similar_returns_list(self, client):
        sample = _upload(client, font_name="Helvetica", style="Sans-Serif", theme="Modern")
        _upload(client, font_name="Arial", style="Sans-Serif", theme="Modern")
        resp = client.get(f"/api/v1/fonts/{sample['id']}/similar")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_similar_excludes_self(self, client):
        sample = _upload(client, font_name="Helvetica", style="Sans-Serif")
        _upload(client, font_name="Arial", style="Sans-Serif")
        resp = client.get(f"/api/v1/fonts/{sample['id']}/similar")
        ids = [e["id"] for e in resp.json()]
        assert sample["id"] not in ids

    def test_similar_includes_score(self, client):
        sample = _upload(client, font_name="Helvetica", style="Sans-Serif")
        _upload(client, font_name="Arial", style="Sans-Serif")
        resp = client.get(f"/api/v1/fonts/{sample['id']}/similar")
        entry = resp.json()[0]
        assert "similarity_score" in entry
        assert 0.0 <= entry["similarity_score"] <= 1.0

    def test_similar_style_match_scores_higher_than_no_match(self, client):
        target = _upload(client, font_name="Helvetica", style="Sans-Serif", theme="Modern")
        _upload(client, font_name="Arial", style="Sans-Serif", theme="Modern")
        _upload(client, font_name="Bodoni", style="Serif", theme="Elegant")
        resp = client.get(f"/api/v1/fonts/{target['id']}/similar")
        entries = resp.json()
        # Arial should be more similar than Bodoni
        arial = next(e for e in entries if e["font_name"] == "Arial")
        bodoni = next(e for e in entries if e["font_name"] == "Bodoni")
        assert arial["similarity_score"] > bodoni["similarity_score"]

    def test_similar_min_score_filter(self, client):
        sample = _upload(client, font_name="Helvetica", style="Sans-Serif")
        _upload(client, font_name="Bodoni")  # no matching fields -> score = 0
        resp = client.get(f"/api/v1/fonts/{sample['id']}/similar?min_score=0.1")
        # Bodoni has score 0 and should be excluded
        for entry in resp.json():
            assert entry["similarity_score"] >= 0.1

    def test_similar_limit_param(self, client):
        target = _upload(client, font_name="Helvetica", style="Sans-Serif")
        for i in range(5):
            _upload(client, font_name=f"Similar{i}", style="Sans-Serif")
        resp = client.get(f"/api/v1/fonts/{target['id']}/similar?limit=3")
        assert len(resp.json()) <= 3

    def test_similar_missing_font_returns_404(self, client):
        resp = client.get("/api/v1/fonts/99999/similar")
        assert resp.status_code == 404

    def test_similar_empty_catalog(self, client):
        sample = _upload(client, font_name="Helvetica")
        resp = client.get(f"/api/v1/fonts/{sample['id']}/similar")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_similar_tag_jaccard_contributes_to_score(self, client):
        target = _upload(client, font_name="Futura", tags="geometric,modern")
        match = _upload(client, font_name="Avant Garde", tags="geometric,modern")
        no_match = _upload(client, font_name="Garamond", tags="serif,classic")
        resp = client.get(f"/api/v1/fonts/{target['id']}/similar")
        entries = {e["id"]: e["similarity_score"] for e in resp.json()}
        assert entries[match["id"]] > entries[no_match["id"]]


# ---------------------------------------------------------------------------
# Issue #30 – GET /api/v1/fonts/{id}/preview – preview config
# ---------------------------------------------------------------------------

class TestV1PreviewConfig:
    def test_preview_returns_200(self, client):
        sample = _upload(client, font_name="Bodoni")
        resp = client.get(f"/api/v1/fonts/{sample['id']}/preview")
        assert resp.status_code == 200

    def test_preview_shape(self, client):
        sample = _upload(client, font_name="Garamond")
        resp = client.get(f"/api/v1/fonts/{sample['id']}/preview")
        body = resp.json()
        assert body["sample_id"] == sample["id"]
        assert "preview_url" in body
        assert "specimen_url" in body
        assert "embed_url" in body
        assert "available_chars" in body
        assert "suggested_text" in body

    def test_preview_url_matches_upload(self, client):
        sample = _upload(client, font_name="Futura")
        resp = client.get(f"/api/v1/fonts/{sample['id']}/preview")
        assert resp.json()["preview_url"] == f"/uploads/{sample['filename']}"

    def test_preview_specimen_url_points_to_print_preview(self, client):
        sample = _upload(client, font_name="Futura")
        resp = client.get(f"/api/v1/fonts/{sample['id']}/preview")
        assert f"/api/samples/{sample['id']}/print-preview" in resp.json()["specimen_url"]

    def test_preview_missing_font_returns_404(self, client):
        resp = client.get("/api/v1/fonts/99999/preview")
        assert resp.status_code == 404
