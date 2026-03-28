"""Tests for the font sample image ingestion and metadata API."""

import io

import pytest

from tests.conftest import make_image_bytes


# ---------------------------------------------------------------------------
# Upload (POST /api/samples/)
# ---------------------------------------------------------------------------

class TestUpload:
    def test_upload_png_success(self, client):
        resp = client.post(
            "/api/samples/",
            files={"file": ("sample.png", io.BytesIO(make_image_bytes()), "image/png")},
            data={"font_name": "Helvetica", "font_category": "sans-serif", "tags": "bold,display"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["font_name"] == "Helvetica"
        assert body["font_category"] == "sans-serif"
        assert set(body["tags"]) == {"bold", "display"}
        assert body["original_filename"] == "sample.png"
        assert body["content_type"] == "image/png"
        assert body["file_size"] > 0
        assert "id" in body
        assert "uploaded_at" in body

    def test_upload_jpeg_success(self, client):
        resp = client.post(
            "/api/samples/",
            files={"file": ("scan.jpg", io.BytesIO(make_image_bytes()), "image/jpeg")},
        )
        assert resp.status_code == 201
        assert resp.json()["content_type"] == "image/jpeg"

    def test_upload_invalid_type_rejected(self, client):
        resp = client.post(
            "/api/samples/",
            files={"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
        )
        assert resp.status_code == 400
        assert "Unsupported file type" in resp.json()["detail"]

    def test_upload_no_file_rejected(self, client):
        resp = client.post("/api/samples/", data={"font_name": "Test"})
        assert resp.status_code == 422

    def test_upload_with_notes(self, client):
        resp = client.post(
            "/api/samples/",
            files={"file": ("n.png", io.BytesIO(make_image_bytes()), "image/png")},
            data={"notes": "Hand-lettered specimen"},
        )
        assert resp.status_code == 201
        assert resp.json()["notes"] == "Hand-lettered specimen"

    def test_upload_with_provenance(self, client):
        resp = client.post(
            "/api/samples/",
            files={"file": ("p.png", io.BytesIO(make_image_bytes()), "image/png")},
            data={
                "source": "https://example.com/archive/scan42.png",
                "restoration_notes": "Despeckled and contrast-adjusted",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["source"] == "https://example.com/archive/scan42.png"
        assert body["restoration_notes"] == "Despeckled and contrast-adjusted"

    def test_upload_without_provenance_defaults_to_null(self, client):
        resp = client.post(
            "/api/samples/",
            files={"file": ("np.png", io.BytesIO(make_image_bytes()), "image/png")},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["source"] is None
        assert body["restoration_notes"] is None


# ---------------------------------------------------------------------------
# Listing (GET /api/samples/)
# ---------------------------------------------------------------------------

class TestList:
    def _upload(self, client, font_name="Arial", font_category="sans-serif", tags=""):
        client.post(
            "/api/samples/",
            files={"file": ("f.png", io.BytesIO(make_image_bytes()), "image/png")},
            data={"font_name": font_name, "font_category": font_category, "tags": tags},
        )

    def test_list_empty(self, client):
        resp = client.get("/api/samples/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_all(self, client):
        self._upload(client, "Arial")
        self._upload(client, "Times New Roman", "serif")
        resp = client.get("/api/samples/")
        assert len(resp.json()) == 2

    def test_filter_by_font_name(self, client):
        self._upload(client, "Arial")
        self._upload(client, "Times New Roman", "serif")
        resp = client.get("/api/samples/?font_name=arial")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["font_name"] == "Arial"

    def test_filter_by_category_exact(self, client):
        self._upload(client, "Arial", "sans-serif")
        self._upload(client, "Times New Roman", "serif")
        # Exact full-word match: only "serif" category
        resp = client.get("/api/samples/?font_category=sans-serif")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["font_name"] == "Arial"

    def test_filter_by_category_substring(self, client):
        self._upload(client, "Arial", "sans-serif")
        self._upload(client, "Times New Roman", "serif")
        # Substring match: "serif" matches both "sans-serif" and "serif"
        resp = client.get("/api/samples/?font_category=serif")
        assert len(resp.json()) == 2

    def test_filter_by_tag(self, client):
        self._upload(client, "Futura", tags="geometric,modern")
        self._upload(client, "Garamond", tags="oldstyle")
        resp = client.get("/api/samples/?tag=geometric")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["font_name"] == "Futura"


# ---------------------------------------------------------------------------
# Detail (GET /api/samples/{id})
# ---------------------------------------------------------------------------

class TestDetail:
    def test_get_existing(self, client):
        up = client.post(
            "/api/samples/",
            files={"file": ("d.png", io.BytesIO(make_image_bytes()), "image/png")},
            data={"font_name": "Bodoni"},
        )
        sample_id = up.json()["id"]
        resp = client.get(f"/api/samples/{sample_id}")
        assert resp.status_code == 200
        assert resp.json()["font_name"] == "Bodoni"

    def test_get_not_found(self, client):
        resp = client.get("/api/samples/99999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Update (PATCH /api/samples/{id})
# ---------------------------------------------------------------------------

class TestUpdate:
    def test_update_metadata(self, client):
        up = client.post(
            "/api/samples/",
            files={"file": ("u.png", io.BytesIO(make_image_bytes()), "image/png")},
            data={"font_name": "Old Name"},
        )
        sample_id = up.json()["id"]
        resp = client.patch(
            f"/api/samples/{sample_id}",
            json={"font_name": "New Name", "tags": ["updated"]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["font_name"] == "New Name"
        assert body["tags"] == ["updated"]

    def test_update_provenance(self, client):
        up = client.post(
            "/api/samples/",
            files={"file": ("up.png", io.BytesIO(make_image_bytes()), "image/png")},
        )
        sample_id = up.json()["id"]
        resp = client.patch(
            f"/api/samples/{sample_id}",
            json={
                "source": "Internet Archive scan #7",
                "restoration_notes": "Auto-levelled",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["source"] == "Internet Archive scan #7"
        assert body["restoration_notes"] == "Auto-levelled"

    def test_update_not_found(self, client):
        resp = client.patch("/api/samples/99999", json={"font_name": "X"})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Delete (DELETE /api/samples/{id})
# ---------------------------------------------------------------------------

class TestDelete:
    def test_delete_existing(self, client):
        up = client.post(
            "/api/samples/",
            files={"file": ("del.png", io.BytesIO(make_image_bytes()), "image/png")},
        )
        sample_id = up.json()["id"]
        resp = client.delete(f"/api/samples/{sample_id}")
        assert resp.status_code == 204
        assert client.get(f"/api/samples/{sample_id}").status_code == 404

    def test_delete_not_found(self, client):
        resp = client.delete("/api/samples/99999")
        assert resp.status_code == 404
