"""Tests for API authentication."""
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.models import Building


class TestAPIKeyAuthentication:
    """Tests for API key authentication."""

    def test_valid_api_key(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test request with valid API key succeeds."""
        response = client.get("/api/v1/buildings", headers=auth_headers)
        assert response.status_code == 200

    def test_missing_api_key(
        self,
        client: TestClient,
        sample_buildings: list[Building],
    ):
        """Test request without API key fails with 422."""
        response = client.get("/api/v1/buildings")
        assert response.status_code == 422  # Validation error - missing required header

    def test_invalid_api_key(
        self,
        client: TestClient,
        sample_buildings: list[Building],
    ):
        """Test request with invalid API key fails with 403."""
        invalid_headers = {"X-API-Key": "invalid-key-12345"}
        response = client.get("/api/v1/buildings", headers=invalid_headers)
        assert response.status_code == 403
        assert "Invalid API Key" in response.json()["detail"]

    def test_empty_api_key(
        self,
        client: TestClient,
        sample_buildings: list[Building],
    ):
        """Test request with empty API key fails."""
        empty_headers = {"X-API-Key": ""}
        response = client.get("/api/v1/buildings", headers=empty_headers)
        assert response.status_code == 403

    def test_case_sensitive_header(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test that API key header is case-insensitive (FastAPI behavior)."""
        # FastAPI normalizes headers to lowercase internally
        lowercase_headers = {"x-api-key": settings.API_KEY}
        response = client.get("/api/v1/buildings", headers=lowercase_headers)
        assert response.status_code == 200


class TestAuthenticationOnAllEndpoints:
    """Test that all endpoints require authentication."""

    def test_organizations_list_requires_auth(self, client: TestClient):
        """Test GET /api/v1/organizations requires auth."""
        response = client.get("/api/v1/organizations")
        assert response.status_code == 422

    def test_organizations_detail_requires_auth(self, client: TestClient):
        """Test GET /api/v1/organizations/{id} requires auth."""
        response = client.get("/api/v1/organizations/1")
        assert response.status_code == 422

    def test_buildings_list_requires_auth(self, client: TestClient):
        """Test GET /api/v1/buildings requires auth."""
        response = client.get("/api/v1/buildings")
        assert response.status_code == 422

    def test_buildings_detail_requires_auth(self, client: TestClient):
        """Test GET /api/v1/buildings/{id} requires auth."""
        response = client.get("/api/v1/buildings/1")
        assert response.status_code == 422

    def test_activities_list_requires_auth(self, client: TestClient):
        """Test GET /api/v1/activities requires auth."""
        response = client.get("/api/v1/activities")
        assert response.status_code == 422

    def test_activities_detail_requires_auth(self, client: TestClient):
        """Test GET /api/v1/activities/{id} requires auth."""
        response = client.get("/api/v1/activities/1")
        assert response.status_code == 422


class TestAuthenticationWithInvalidKey:
    """Test that all endpoints reject invalid API keys."""

    def setup_method(self):
        """Set up invalid headers for tests."""
        self.invalid_headers = {"X-API-Key": "wrong-key"}

    def test_organizations_list_rejects_invalid_key(
        self, client: TestClient, sample_buildings: list[Building]
    ):
        """Test GET /api/v1/organizations rejects invalid key."""
        response = client.get("/api/v1/organizations", headers=self.invalid_headers)
        assert response.status_code == 403

    def test_organizations_detail_rejects_invalid_key(
        self, client: TestClient, sample_buildings: list[Building]
    ):
        """Test GET /api/v1/organizations/{id} rejects invalid key."""
        response = client.get("/api/v1/organizations/1", headers=self.invalid_headers)
        assert response.status_code == 403

    def test_buildings_list_rejects_invalid_key(
        self, client: TestClient, sample_buildings: list[Building]
    ):
        """Test GET /api/v1/buildings rejects invalid key."""
        response = client.get("/api/v1/buildings", headers=self.invalid_headers)
        assert response.status_code == 403

    def test_buildings_detail_rejects_invalid_key(
        self, client: TestClient, sample_buildings: list[Building]
    ):
        """Test GET /api/v1/buildings/{id} rejects invalid key."""
        response = client.get("/api/v1/buildings/1", headers=self.invalid_headers)
        assert response.status_code == 403

    def test_activities_list_rejects_invalid_key(
        self, client: TestClient, sample_buildings: list[Building]
    ):
        """Test GET /api/v1/activities rejects invalid key."""
        response = client.get("/api/v1/activities", headers=self.invalid_headers)
        assert response.status_code == 403

    def test_activities_detail_rejects_invalid_key(
        self, client: TestClient, sample_buildings: list[Building]
    ):
        """Test GET /api/v1/activities/{id} rejects invalid key."""
        response = client.get("/api/v1/activities/1", headers=self.invalid_headers)
        assert response.status_code == 403


class TestDocumentationEndpoints:
    """Test that documentation endpoints don't require authentication."""

    def test_openapi_json_public(self, client: TestClient):
        """Test that OpenAPI JSON is publicly accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data

    def test_swagger_ui_public(self, client: TestClient):
        """Test that Swagger UI is publicly accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_public(self, client: TestClient):
        """Test that ReDoc is publicly accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200
