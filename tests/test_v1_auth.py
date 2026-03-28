"""Tests for API key provisioning, rate limiting, and auth (issue #31)."""

import time
from unittest.mock import patch

import pytest


class TestApiKeyProvisioning:
    def test_create_api_key(self, client):
        resp = client.post(
            "/api/v1/keys",
            json={"owner": "test-partner", "scope": "read", "rate_limit": 500},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["owner"] == "test-partner"
        assert body["scope"] == "read"
        assert body["rate_limit"] == 500
        assert body["is_active"] is True
        assert len(body["key"]) > 20

    def test_create_admin_key(self, client):
        resp = client.post(
            "/api/v1/keys",
            json={"owner": "admin-user", "scope": "admin"},
        )
        assert resp.status_code == 201
        assert resp.json()["scope"] == "admin"

    def test_list_api_keys(self, client):
        client.post("/api/v1/keys", json={"owner": "owner-a", "scope": "read"})
        client.post("/api/v1/keys", json={"owner": "owner-b", "scope": "write"})
        resp = client.get("/api/v1/keys")
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_revoke_api_key(self, client):
        create_resp = client.post("/api/v1/keys", json={"owner": "to-revoke", "scope": "read"})
        key_id = create_resp.json()["id"]
        revoke_resp = client.delete(f"/api/v1/keys/{key_id}")
        assert revoke_resp.status_code == 204
        # Verify it is now inactive
        keys = client.get("/api/v1/keys").json()
        matching = [k for k in keys if k["id"] == key_id]
        assert len(matching) == 1
        assert matching[0]["is_active"] is False

    def test_revoke_missing_key_returns_404(self, client):
        resp = client.delete("/api/v1/keys/99999")
        assert resp.status_code == 404

    def test_keys_have_unique_values(self, client):
        r1 = client.post("/api/v1/keys", json={"owner": "a", "scope": "read"})
        r2 = client.post("/api/v1/keys", json={"owner": "b", "scope": "read"})
        assert r1.json()["key"] != r2.json()["key"]


class TestApiKeyAuthentication:
    def test_valid_key_accepted_by_v1_endpoint(self, client):
        """A valid API key in X-API-Key header should be accepted."""
        create_resp = client.post("/api/v1/keys", json={"owner": "partner", "scope": "read"})
        key = create_resp.json()["key"]
        resp = client.get("/api/v1/fonts", headers={"X-API-Key": key})
        assert resp.status_code == 200

    def test_revoked_key_rejected(self, client):
        """A revoked key should return 401."""
        create_resp = client.post("/api/v1/keys", json={"owner": "partner", "scope": "read"})
        key_id = create_resp.json()["id"]
        key = create_resp.json()["key"]
        client.delete(f"/api/v1/keys/{key_id}")
        resp = client.get("/api/v1/fonts", headers={"X-API-Key": key})
        assert resp.status_code == 401

    def test_invalid_key_rejected(self, client):
        """An unrecognised key should return 401."""
        resp = client.get("/api/v1/fonts", headers={"X-API-Key": "totally-invalid-key"})
        assert resp.status_code == 401

    def test_anonymous_access_allowed_for_catalog(self, client):
        """Anonymous access (no key) to catalog endpoints is allowed."""
        resp = client.get("/api/v1/fonts")
        # May be 200 or 429 if prior tests consumed the limit; just check not 401
        assert resp.status_code in (200, 429)


class TestRateLimiting:
    def test_rate_limit_exceeded(self, client):
        """Calls beyond the rate limit should return 429."""
        create_resp = client.post(
            "/api/v1/keys",
            json={"owner": "limited-partner", "scope": "read", "rate_limit": 2},
        )
        key = create_resp.json()["key"]

        from app import auth as auth_module

        # Patch the window to be very short so we don't have to wait
        with patch.object(auth_module, "_WINDOW_SECONDS", 3600):
            # Clear any prior log for this key
            auth_module._REQUEST_LOG.pop(key, None)

            r1 = client.get("/api/v1/fonts", headers={"X-API-Key": key})
            r2 = client.get("/api/v1/fonts", headers={"X-API-Key": key})
            r3 = client.get("/api/v1/fonts", headers={"X-API-Key": key})

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r3.status_code == 429
        assert "Rate limit exceeded" in r3.json()["detail"]

    def test_rate_limit_resets_after_window(self, client):
        """After the window expires, requests should be accepted again."""
        create_resp = client.post(
            "/api/v1/keys",
            json={"owner": "resetting-partner", "scope": "read", "rate_limit": 1},
        )
        key = create_resp.json()["key"]

        from app import auth as auth_module

        auth_module._REQUEST_LOG.pop(key, None)

        # Use up the quota
        r1 = client.get("/api/v1/fonts", headers={"X-API-Key": key})
        assert r1.status_code == 200

        # Simulate the window having elapsed by back-dating the timestamp
        auth_module._REQUEST_LOG[key] = [time.time() - 3601]

        r2 = client.get("/api/v1/fonts", headers={"X-API-Key": key})
        assert r2.status_code == 200
