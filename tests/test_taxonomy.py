"""Tests for the font taxonomy endpoint and style/theme filtering."""

import io

import pytest

from app.taxonomy import (
    CATEGORIES,
    CONSTRUCTION_TRAITS,
    ERAS,
    GENRES,
    HIERARCHY,
    MOODS,
    ORIGIN_CONTEXTS,
    RESTORATION_STATUSES,
    RIGHTS_STATUSES,
    SOURCE_TYPES,
    STYLES,
    SYNONYMS,
    THEMES,
    USE_CASES,
    VISUAL_TRAITS,
    FIELD_CONFIG,
    expand_synonyms,
    get_field_config,
    get_hierarchy,
    get_synonyms,
    get_taxonomy,
)
from tests.conftest import make_image_bytes


# ---------------------------------------------------------------------------
# Taxonomy data – core dimensions
# ---------------------------------------------------------------------------

class TestTaxonomyData:
    def test_styles_not_empty(self):
        assert len(STYLES) > 0

    def test_themes_not_empty(self):
        assert len(THEMES) > 0

    def test_categories_not_empty(self):
        assert len(CATEGORIES) > 0

    def test_genres_not_empty(self):
        assert len(GENRES) > 0

    def test_moods_not_empty(self):
        assert len(MOODS) > 0

    def test_use_cases_not_empty(self):
        assert len(USE_CASES) > 0

    def test_eras_not_empty(self):
        assert len(ERAS) > 0

    def test_origin_contexts_not_empty(self):
        assert len(ORIGIN_CONTEXTS) > 0

    def test_construction_traits_not_empty(self):
        assert len(CONSTRUCTION_TRAITS) > 0

    def test_visual_traits_not_empty(self):
        assert len(VISUAL_TRAITS) > 0

    def test_restoration_statuses_not_empty(self):
        assert len(RESTORATION_STATUSES) > 0

    def test_source_types_not_empty(self):
        assert len(SOURCE_TYPES) > 0

    def test_rights_statuses_not_empty(self):
        assert len(RIGHTS_STATUSES) > 0

    def test_get_taxonomy_returns_all_keys(self):
        tax = get_taxonomy()
        expected_keys = {
            "styles", "genres", "themes", "moods", "categories", "use_cases",
            "eras", "origin_contexts", "construction_traits", "visual_traits",
            "restoration_statuses", "source_types", "rights_statuses",
        }
        assert expected_keys.issubset(set(tax.keys()))
        assert tax["styles"] == STYLES
        assert tax["themes"] == THEMES
        assert tax["categories"] == CATEGORIES

    def test_get_taxonomy_new_dimensions(self):
        tax = get_taxonomy()
        assert tax["genres"] == GENRES
        assert tax["moods"] == MOODS
        assert tax["use_cases"] == USE_CASES
        assert tax["eras"] == ERAS
        assert tax["origin_contexts"] == ORIGIN_CONTEXTS
        assert tax["construction_traits"] == CONSTRUCTION_TRAITS
        assert tax["visual_traits"] == VISUAL_TRAITS
        assert tax["restoration_statuses"] == RESTORATION_STATUSES
        assert tax["source_types"] == SOURCE_TYPES
        assert tax["rights_statuses"] == RIGHTS_STATUSES


# ---------------------------------------------------------------------------
# Hierarchy
# ---------------------------------------------------------------------------

class TestTaxonomyHierarchy:
    def test_hierarchy_not_empty(self):
        h = get_hierarchy()
        assert len(h) > 0

    def test_hierarchy_serif_has_children(self):
        h = get_hierarchy()
        assert "Serif" in h
        assert len(h["Serif"]) > 0

    def test_hierarchy_sans_serif_has_children(self):
        h = get_hierarchy()
        assert "Sans-Serif" in h
        assert len(h["Sans-Serif"]) > 0

    def test_hierarchy_children_are_genres(self):
        h = get_hierarchy()
        for children in h.values():
            for child in children:
                assert child in GENRES


# ---------------------------------------------------------------------------
# Synonyms
# ---------------------------------------------------------------------------

class TestTaxonomySynonyms:
    def test_synonyms_not_empty(self):
        s = get_synonyms()
        assert len(s) > 0

    def test_expand_synonyms_canonical(self):
        result = expand_synonyms("Sans-Serif")
        assert "Sans-Serif" in result
        assert len(result) > 1

    def test_expand_synonyms_synonym_lookup(self):
        result = expand_synonyms("grotesque")
        assert "Sans-Serif" in result

    def test_expand_synonyms_unknown_term(self):
        result = expand_synonyms("CompletelyUnknownTerm")
        assert result == ["CompletelyUnknownTerm"]


# ---------------------------------------------------------------------------
# Field configuration
# ---------------------------------------------------------------------------

class TestFieldConfig:
    def test_field_config_not_empty(self):
        fc = get_field_config()
        assert len(fc) > 0

    def test_style_is_single_select(self):
        fc = get_field_config()
        assert fc["style"]["cardinality"] == "single"

    def test_moods_is_multi_select(self):
        fc = get_field_config()
        assert fc["moods"]["cardinality"] == "multi"

    def test_visual_traits_is_multi_select(self):
        fc = get_field_config()
        assert fc["visual_traits"]["cardinality"] == "multi"

    def test_era_is_single_select(self):
        fc = get_field_config()
        assert fc["era"]["cardinality"] == "single"

    def test_field_config_has_required_keys(self):
        fc = get_field_config()
        for field, config in fc.items():
            assert "label" in config
            assert "values" in config
            assert "cardinality" in config
            assert config["cardinality"] in ("single", "multi")


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

    def test_taxonomy_new_dimensions_present(self, client):
        resp = client.get("/api/taxonomy/")
        body = resp.json()
        for key in ["genres", "moods", "use_cases", "eras", "origin_contexts",
                    "construction_traits", "visual_traits", "restoration_statuses",
                    "source_types", "rights_statuses"]:
            assert key in body, f"Missing taxonomy key: {key}"
            assert isinstance(body[key], list)
            assert len(body[key]) > 0

    def test_taxonomy_values_match_module(self, client):
        resp = client.get("/api/taxonomy/")
        body = resp.json()
        assert body["styles"] == STYLES
        assert body["themes"] == THEMES
        assert body["categories"] == CATEGORIES

    def test_get_taxonomy_hierarchy(self, client):
        resp = client.get("/api/taxonomy/hierarchy")
        assert resp.status_code == 200
        body = resp.json()
        assert "Serif" in body
        assert "Sans-Serif" in body
        assert isinstance(body["Serif"], list)

    def test_get_taxonomy_synonyms(self, client):
        resp = client.get("/api/taxonomy/synonyms")
        assert resp.status_code == 200
        body = resp.json()
        assert "Sans-Serif" in body
        assert isinstance(body["Sans-Serif"], list)

    def test_get_taxonomy_fields(self, client):
        resp = client.get("/api/taxonomy/fields")
        assert resp.status_code == 200
        body = resp.json()
        assert "style" in body
        assert body["style"]["cardinality"] == "single"
        assert "visual_traits" in body
        assert body["visual_traits"]["cardinality"] == "multi"


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

    def test_upload_with_extended_taxonomy_fields(self, client):
        resp = client.post(
            "/api/samples/",
            files={"file": ("s3.png", io.BytesIO(make_image_bytes()), "image/png")},
            data={
                "font_name": "Clarendon",
                "genre": "Slab Serif",
                "origin_context": "British",
                "source_type": "Printed Specimen",
                "restoration_status": "Cleaned",
                "rights_status": "Public Domain",
                "completeness": "0.8",
                "moods": "Bold,Classic",
                "use_cases": "Poster,Headline",
                "construction_traits": "High Contrast,Slab Serif",
                "visual_traits": "High Contrast,Slab Serif",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["genre"] == "Slab Serif"
        assert body["origin_context"] == "British"
        assert body["source_type"] == "Printed Specimen"
        assert body["restoration_status"] == "Cleaned"
        assert body["rights_status"] == "Public Domain"
        assert body["completeness"] == 0.8
        assert "Bold" in body["moods"]
        assert "Poster" in body["use_cases"]
        assert "High Contrast" in body["construction_traits"]
        assert "High Contrast" in body["visual_traits"]

    def test_upload_moods_and_visual_traits_default_empty(self, client):
        resp = client.post(
            "/api/samples/",
            files={"file": ("s4.png", io.BytesIO(make_image_bytes()), "image/png")},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["moods"] == []
        assert body["visual_traits"] == []
        assert body["use_cases"] == []
        assert body["construction_traits"] == []


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

    def test_update_extended_taxonomy_fields(self, client):
        up = client.post(
            "/api/samples/",
            files={"file": ("u2.png", io.BytesIO(make_image_bytes()), "image/png")},
            data={"font_name": "Old Font"},
        )
        sample_id = up.json()["id"]
        resp = client.patch(
            f"/api/samples/{sample_id}",
            json={
                "genre": "Old Style",
                "origin_context": "French",
                "source_type": "Type Catalogue",
                "restoration_status": "Outlined",
                "rights_status": "Public Domain",
                "rights_notes": "Pre-1923 publication",
                "completeness": 0.9,
                "moods": ["Classic", "Elegant"],
                "use_cases": ["Body Text", "Editorial Layout"],
                "visual_traits": ["High Contrast", "Bracketed Serif"],
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["genre"] == "Old Style"
        assert body["origin_context"] == "French"
        assert body["source_type"] == "Type Catalogue"
        assert body["restoration_status"] == "Outlined"
        assert body["rights_status"] == "Public Domain"
        assert body["rights_notes"] == "Pre-1923 publication"
        assert body["completeness"] == 0.9
        assert "Classic" in body["moods"]
        assert "Body Text" in body["use_cases"]
        assert "High Contrast" in body["visual_traits"]


# ---------------------------------------------------------------------------
# v1 search – new filter parameters
# ---------------------------------------------------------------------------

class TestV1TaxonomyFilters:
    def _upload_v1(self, client, font_name, genre=None, origin_context=None,
                   restoration_status=None, rights_status=None):
        data = {"font_name": font_name}
        if genre:
            data["genre"] = genre
        if origin_context:
            data["origin_context"] = origin_context
        if restoration_status:
            data["restoration_status"] = restoration_status
        if rights_status:
            data["rights_status"] = rights_status
        resp = client.post(
            "/api/samples/",
            files={"file": ("v.png", io.BytesIO(make_image_bytes()), "image/png")},
            data=data,
        )
        assert resp.status_code == 201
        return resp.json()

    def test_filter_by_genre(self, client):
        self._upload_v1(client, "Garamond", genre="Old Style")
        self._upload_v1(client, "Bodoni", genre="Modern")
        resp = client.get("/api/v1/fonts?genre=Old+Style")
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["font_name"] == "Garamond"

    def test_filter_by_origin_context(self, client):
        self._upload_v1(client, "Helvetica", origin_context="Swiss")
        self._upload_v1(client, "Gill Sans", origin_context="British")
        resp = client.get("/api/v1/fonts?origin_context=Swiss")
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["font_name"] == "Helvetica"

    def test_filter_by_restoration_status(self, client):
        self._upload_v1(client, "Clarendon", restoration_status="Complete")
        self._upload_v1(client, "Windsor", restoration_status="Raw Scan")
        resp = client.get("/api/v1/fonts?restoration_status=Complete")
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["font_name"] == "Clarendon"

    def test_filter_by_rights_status(self, client):
        self._upload_v1(client, "Caslon", rights_status="Public Domain")
        self._upload_v1(client, "Futura", rights_status="Commercial License")
        resp = client.get("/api/v1/fonts?rights_status=Public+Domain")
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["font_name"] == "Caslon"

    def test_search_by_genre(self, client):
        self._upload_v1(client, "Baskerville", genre="Transitional")
        self._upload_v1(client, "Helvetica", genre="Neo-Grotesque")
        resp = client.get("/api/v1/fonts/search?genre=Transitional")
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["font_name"] == "Baskerville"

    def test_search_freetext_matches_origin_context(self, client):
        self._upload_v1(client, "Akzidenz", origin_context="German")
        resp = client.get("/api/v1/fonts/search?q=German")
        assert resp.json()["total"] == 1

    def test_similar_fonts_include_visual_traits(self, client):
        import io as _io
        up = client.post(
            "/api/samples/",
            files={"file": ("sim1.png", _io.BytesIO(make_image_bytes()), "image/png")},
            data={"font_name": "A", "visual_traits": "High Contrast,Bracketed Serif"},
        )
        target_id = up.json()["id"]
        client.post(
            "/api/samples/",
            files={"file": ("sim2.png", _io.BytesIO(make_image_bytes()), "image/png")},
            data={"font_name": "B", "visual_traits": "High Contrast,Bracketed Serif"},
        )
        resp = client.get(f"/api/v1/fonts/{target_id}/similar")
        assert resp.status_code == 200
        entries = resp.json()
        assert len(entries) == 1
        assert "visual_traits" in entries[0]
        assert entries[0]["similarity_score"] > 0
