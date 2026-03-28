"""Tests for the Vizail and kulrs integration adapter endpoints (issue #17)."""

import io

from tests.conftest import make_image_bytes


def _upload(client, font_name=None, font_category=None, style=None, theme=None, tags=""):
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
    resp = client.post(
        "/api/samples/",
        files={"file": ("f.png", io.BytesIO(make_image_bytes()), "image/png")},
        data=data,
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# GET /api/integrations/vizail
# ---------------------------------------------------------------------------

class TestVizailAdapter:
    def test_vizail_returns_200(self, client):
        resp = client.get("/api/integrations/vizail")
        assert resp.status_code == 200

    def test_vizail_empty_catalog(self, client):
        resp = client.get("/api/integrations/vizail")
        body = resp.json()
        assert "fonts" in body
        assert body["fonts"] == []

    def test_vizail_contains_fonts_key(self, client):
        _upload(client, font_name="Helvetica")
        resp = client.get("/api/integrations/vizail")
        body = resp.json()
        assert "fonts" in body
        assert isinstance(body["fonts"], list)

    def test_vizail_font_entry_fields(self, client):
        sample = _upload(
            client,
            font_name="Helvetica",
            font_category="Sans-Serif",
            style="Sans-Serif",
            theme="Modern",
            tags="clean,corporate",
        )
        resp = client.get("/api/integrations/vizail")
        fonts = resp.json()["fonts"]
        assert len(fonts) == 1
        entry = fonts[0]
        assert entry["id"] == sample["id"]
        assert entry["name"] == "Helvetica"
        assert entry["category"] == "Sans-Serif"
        assert entry["style"] == "Sans-Serif"
        assert entry["theme"] == "Modern"
        assert set(entry["tags"]) == {"clean", "corporate"}
        assert entry["preview_url"] == f"/uploads/{sample['filename']}"
        assert entry["glyph_count"] == 0

    def test_vizail_multiple_fonts(self, client):
        _upload(client, font_name="Arial")
        _upload(client, font_name="Times New Roman")
        resp = client.get("/api/integrations/vizail")
        assert len(resp.json()["fonts"]) == 2


# ---------------------------------------------------------------------------
# GET /api/integrations/kulrs
# ---------------------------------------------------------------------------

class TestKulrsAdapter:
    def test_kulrs_returns_200(self, client):
        resp = client.get("/api/integrations/kulrs")
        assert resp.status_code == 200

    def test_kulrs_empty_catalog(self, client):
        resp = client.get("/api/integrations/kulrs")
        assert resp.json() == []

    def test_kulrs_returns_list(self, client):
        _upload(client, font_name="Futura")
        resp = client.get("/api/integrations/kulrs")
        assert isinstance(resp.json(), list)

    def test_kulrs_font_entry_fields(self, client):
        sample = _upload(
            client,
            font_name="Futura",
            font_category="Sans-Serif",
            style="Sans-Serif",
            theme="Modern",
            tags="geometric",
        )
        resp = client.get("/api/integrations/kulrs")
        entries = resp.json()
        assert len(entries) == 1
        entry = entries[0]
        assert entry["id"] == sample["id"]
        assert entry["name"] == "Futura"
        assert "traits" in entry
        assert entry["traits"]["category"] == "Sans-Serif"
        assert entry["traits"]["style"] == "Sans-Serif"
        assert entry["traits"]["theme"] == "Modern"
        assert entry["tags"] == ["geometric"]
        assert entry["preview_url"] == f"/uploads/{sample['filename']}"

    def test_kulrs_traits_structure(self, client):
        _upload(client, font_name="Garamond", style="Serif", theme="Vintage")
        resp = client.get("/api/integrations/kulrs")
        entry = resp.json()[0]
        assert isinstance(entry["traits"], dict)
        assert set(entry["traits"].keys()) == {"category", "style", "theme"}

    def test_kulrs_multiple_fonts(self, client):
        _upload(client, font_name="Arial")
        _upload(client, font_name="Bodoni")
        resp = client.get("/api/integrations/kulrs")
        assert len(resp.json()) == 2

    def test_kulrs_no_glyph_count_field(self, client):
        """kulrs format does not include glyph_count (unlike Vizail)."""
        _upload(client, font_name="Courier")
        resp = client.get("/api/integrations/kulrs")
        entry = resp.json()[0]
        assert "glyph_count" not in entry
