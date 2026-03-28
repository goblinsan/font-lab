"""Tests for the font taxonomy endpoint and style/theme filtering."""

import io

import pytest

from app.taxonomy import CATEGORIES, STYLES, THEMES, get_taxonomy
from tests.conftest import make_image_bytes


# ---------------------------------------------------------------------------
# Taxonomy data
# ---------------------------------------------------------------------------

class TestTaxonomyData:
    def test_styles_not_empty(self):
        assert len(STYLES) > 0

    def test_themes_not_empty(self):
        assert len(THEMES) > 0

    def test_categories_not_empty(self):
        assert len(CATEGORIES) > 0

    def test_get_taxonomy_returns_all_keys(self):
        tax = get_taxonomy()
        assert set(tax.keys()) == {"styles", "themes", "categories"}
        assert tax["styles"] == STYLES
        assert tax["themes"] == THEMES
        assert tax["categories"] == CATEGORIES


# ---------------------------------------------------------------------------
# Taxonomy API endpoint
# ---------------------------------------------------------------------------

class TestTaxonomyEndpoint:
    def test_get_taxonomy(self, client):
        resp = client.get("/api/taxonomy/")
        assert resp.status_code == 200
        body = resp.json()
        assert "styles" in body
        assert "themes" in body
        assert "categories" in body
        assert isinstance(body["styles"], list)
        assert isinstance(body["themes"], list)
        assert isinstance(body["categories"], list)
        assert len(body["styles"]) > 0
        assert len(body["themes"]) > 0
        assert len(body["categories"]) > 0

    def test_taxonomy_values_match_module(self, client):
        resp = client.get("/api/taxonomy/")
        body = resp.json()
        assert body["styles"] == STYLES
        assert body["themes"] == THEMES
        assert body["categories"] == CATEGORIES


# ---------------------------------------------------------------------------
# Upload with style and theme
# ---------------------------------------------------------------------------

class TestUploadWithTaxonomy:
    def test_upload_with_style_and_theme(self, client):
        resp = client.post(
            "/api/samples/",
            files={"file": ("s.png", io.BytesIO(make_image_bytes()), "image/png")},
            data={"font_name": "Futura", "style": "Sans-Serif", "theme": "Modern"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["style"] == "Sans-Serif"
        assert body["theme"] == "Modern"

    def test_upload_without_style_and_theme(self, client):
        resp = client.post(
            "/api/samples/",
            files={"file": ("s2.png", io.BytesIO(make_image_bytes()), "image/png")},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["style"] is None
        assert body["theme"] is None


# ---------------------------------------------------------------------------
# Filter by style and theme
# ---------------------------------------------------------------------------

class TestFilterByTaxonomy:
    def _upload(self, client, font_name, style=None, theme=None):
        data = {"font_name": font_name}
        if style:
            data["style"] = style
        if theme:
            data["theme"] = theme
        client.post(
            "/api/samples/",
            files={"file": ("f.png", io.BytesIO(make_image_bytes()), "image/png")},
            data=data,
        )

    def test_filter_by_style(self, client):
        self._upload(client, "Helvetica", style="Sans-Serif")
        self._upload(client, "Garamond",  style="Serif")
        resp = client.get("/api/samples/?style=Sans-Serif")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["font_name"] == "Helvetica"

    def test_filter_by_theme(self, client):
        self._upload(client, "Bauhaus", theme="Modern")
        self._upload(client, "Windsor", theme="Vintage")
        resp = client.get("/api/samples/?theme=Vintage")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["font_name"] == "Windsor"

    def test_filter_style_case_insensitive(self, client):
        self._upload(client, "Arial", style="Sans-Serif")
        resp = client.get("/api/samples/?style=sans-serif")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["style"] == "Sans-Serif"

    def test_filter_theme_case_insensitive(self, client):
        self._upload(client, "Playfair", theme="Elegant")
        resp = client.get("/api/samples/?theme=elegant")
        data = resp.json()
        assert len(data) == 1

    def test_filter_style_and_theme_combined(self, client):
        self._upload(client, "Univers",  style="Sans-Serif", theme="Modern")
        self._upload(client, "Caslon",   style="Serif",      theme="Vintage")
        self._upload(client, "Gill Sans",style="Sans-Serif", theme="Vintage")

        resp = client.get("/api/samples/?style=Sans-Serif&theme=Modern")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["font_name"] == "Univers"

    def test_filter_no_match(self, client):
        self._upload(client, "Times", style="Serif")
        resp = client.get("/api/samples/?style=Monospace")
        assert resp.json() == []


# ---------------------------------------------------------------------------
# Update style and theme via PATCH
# ---------------------------------------------------------------------------

class TestUpdateTaxonomy:
    def test_update_style_and_theme(self, client):
        up = client.post(
            "/api/samples/",
            files={"file": ("u.png", io.BytesIO(make_image_bytes()), "image/png")},
            data={"font_name": "Test Font"},
        )
        sample_id = up.json()["id"]
        resp = client.patch(
            f"/api/samples/{sample_id}",
            json={"style": "Display", "theme": "Bold"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["style"] == "Display"
        assert body["theme"] == "Bold"
