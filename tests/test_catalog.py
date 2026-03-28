"""Tests for the font catalog API endpoints (issues #15, #16)."""

import io

from tests.conftest import make_image_bytes


def _upload(client, font_name=None, font_category=None, style=None, theme=None, tags="", notes=None):
    data = {}
    if font_name:
        data["font_name"] = font_name
    if font_category:
        data["font_category"] = font_category
    if style:
        data["style"] = style
    if theme:
        data["theme"] = theme
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
# GET /api/catalog/ – list all entries
# ---------------------------------------------------------------------------

class TestCatalogList:
    def test_empty_catalog(self, client):
        resp = client.get("/api/catalog/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_catalog_returns_all_samples(self, client):
        _upload(client, font_name="Arial")
        _upload(client, font_name="Times New Roman")
        resp = client.get("/api/catalog/")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_catalog_entry_has_preview_url(self, client):
        sample = _upload(client, font_name="Helvetica")
        resp = client.get("/api/catalog/")
        entry = resp.json()[0]
        assert "preview_url" in entry
        assert entry["preview_url"] == f"/uploads/{sample['filename']}"

    def test_catalog_entry_has_glyph_count(self, client):
        _upload(client, font_name="Futura")
        resp = client.get("/api/catalog/")
        entry = resp.json()[0]
        assert "glyph_count" in entry
        assert entry["glyph_count"] == 0


# ---------------------------------------------------------------------------
# GET /api/catalog/{id} – single entry with preview (#16)
# ---------------------------------------------------------------------------

class TestCatalogDetail:
    def test_get_existing_entry(self, client):
        sample = _upload(client, font_name="Bodoni", style="Serif", theme="Elegant")
        resp = client.get(f"/api/catalog/{sample['id']}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["font_name"] == "Bodoni"
        assert body["style"] == "Serif"
        assert body["theme"] == "Elegant"
        assert body["preview_url"] == f"/uploads/{sample['filename']}"
        assert body["glyph_count"] == 0

    def test_get_missing_entry(self, client):
        resp = client.get("/api/catalog/99999")
        assert resp.status_code == 404

    def test_entry_contains_all_metadata_fields(self, client):
        sample = _upload(
            client,
            font_name="Garamond",
            font_category="Serif",
            style="Serif",
            theme="Vintage",
            tags="editorial,elegant",
            notes="Classic typeface",
        )
        resp = client.get(f"/api/catalog/{sample['id']}")
        body = resp.json()
        assert body["font_category"] == "Serif"
        assert set(body["tags"]) == {"editorial", "elegant"}
        assert body["notes"] == "Classic typeface"
        assert "uploaded_at" in body


# ---------------------------------------------------------------------------
# GET /api/catalog/search – query by metadata and traits (#15)
# ---------------------------------------------------------------------------

class TestCatalogSearch:
    def test_search_empty(self, client):
        resp = client.get("/api/catalog/search")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_search_all_returned_without_filters(self, client):
        _upload(client, font_name="Arial")
        _upload(client, font_name="Verdana")
        resp = client.get("/api/catalog/search")
        assert len(resp.json()) == 2

    def test_search_by_font_name(self, client):
        _upload(client, font_name="Helvetica")
        _upload(client, font_name="Garamond")
        resp = client.get("/api/catalog/search?font_name=helv")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["font_name"] == "Helvetica"

    def test_search_by_style(self, client):
        _upload(client, font_name="Helvetica", style="Sans-Serif")
        _upload(client, font_name="Garamond", style="Serif")
        resp = client.get("/api/catalog/search?style=Sans-Serif")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["font_name"] == "Helvetica"

    def test_search_by_theme(self, client):
        _upload(client, font_name="Bauhaus", theme="Modern")
        _upload(client, font_name="Windsor", theme="Vintage")
        resp = client.get("/api/catalog/search?theme=Vintage")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["font_name"] == "Windsor"

    def test_search_by_font_category(self, client):
        _upload(client, font_name="Courier", font_category="Monospace")
        _upload(client, font_name="Arial", font_category="Sans-Serif")
        resp = client.get("/api/catalog/search?font_category=Monospace")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["font_name"] == "Courier"

    def test_search_by_tag(self, client):
        _upload(client, font_name="Futura", tags="geometric,modern")
        _upload(client, font_name="Baskerville", tags="classic")
        resp = client.get("/api/catalog/search?tag=geometric")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["font_name"] == "Futura"

    def test_search_freetext_q_matches_font_name(self, client):
        _upload(client, font_name="Optima")
        _upload(client, font_name="Verdana")
        resp = client.get("/api/catalog/search?q=optima")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["font_name"] == "Optima"

    def test_search_freetext_q_matches_style(self, client):
        _upload(client, font_name="Arial", style="Sans-Serif")
        _upload(client, font_name="Times", style="Serif")
        resp = client.get("/api/catalog/search?q=Sans-Serif")
        data = resp.json()
        assert len(data) == 1

    def test_search_freetext_q_matches_notes(self, client):
        _upload(client, font_name="SpecialFont", notes="handcrafted specimen")
        _upload(client, font_name="OtherFont", notes="digital design")
        resp = client.get("/api/catalog/search?q=handcrafted")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["font_name"] == "SpecialFont"

    def test_search_combined_filters(self, client):
        _upload(client, font_name="Univers", style="Sans-Serif", theme="Modern")
        _upload(client, font_name="Caslon", style="Serif", theme="Vintage")
        _upload(client, font_name="Gill Sans", style="Sans-Serif", theme="Vintage")
        resp = client.get("/api/catalog/search?style=Sans-Serif&theme=Modern")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["font_name"] == "Univers"

    def test_search_no_match_returns_empty(self, client):
        _upload(client, font_name="Arial", style="Sans-Serif")
        resp = client.get("/api/catalog/search?style=Blackletter")
        assert resp.json() == []

    def test_search_results_include_preview_url(self, client):
        sample = _upload(client, font_name="Futura")
        resp = client.get("/api/catalog/search?font_name=Futura")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["preview_url"] == f"/uploads/{sample['filename']}"
