"""Tests for building endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.models.models import Building


class TestBuildingsList:
    """Tests for GET /api/v1/buildings endpoint."""

    def test_get_all_buildings(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test getting all buildings."""
        response = client.get("/api/v1/buildings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(building["address"] for building in data)
        assert all(building["cadastral_number"] for building in data)

    def test_filter_by_address(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test filtering buildings by address substring."""
        response = client.get("/api/v1/buildings?address=Москва", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("Москва" in building["address"] for building in data)

        response = client.get(
            "/api/v1/buildings?address=Ленина", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Ленина" in data[0]["address"]

    def test_filter_by_postcode(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test filtering buildings by postcode."""
        response = client.get("/api/v1/buildings?postcode=101000", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["postcode"] == "101000"

    def test_filter_by_cadastral_number(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test filtering buildings by cadastral number substring."""
        response = client.get(
            "/api/v1/buildings?cadastral_number=77:01", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Both Moscow buildings
        assert all(building["cadastral_number"].startswith("77:01") for building in data)

    def test_geo_search_radius(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test geo-search buildings by radius."""
        # Search near first Moscow building
        response = client.get(
            "/api/v1/buildings?lat=55.7558&lon=37.6173&radius=1000",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Both Moscow buildings within 1km

        # Very small radius
        response = client.get(
            "/api/v1/buildings?lat=55.7558&lon=37.6173&radius=10",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Only the nearest building

    def test_geo_search_bounding_box(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test geo-search buildings by bounding box."""
        # Box around Moscow
        response = client.get(
            "/api/v1/buildings?lat_min=55.7&lat_max=55.8&lon_min=37.5&lon_max=37.7",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Box around St. Petersburg
        response = client.get(
            "/api/v1/buildings?lat_min=59.9&lat_max=60.0&lon_min=30.3&lon_max=30.4",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Санкт-Петербург" in data[0]["address"]

    def test_combined_filters(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test combining multiple filters."""
        response = client.get(
            "/api/v1/buildings?address=Москва&postcode=101000",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Москва" in data[0]["address"]
        assert data[0]["postcode"] == "101000"


class TestBuildingDetail:
    """Tests for GET /api/v1/buildings/{id} endpoint."""

    def test_get_building_by_id(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test getting building by ID."""
        building_id = sample_buildings[0].id
        response = client.get(f"/api/v1/buildings/{building_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == building_id
        assert "Москва" in data["address"]
        assert data["cadastral_number"] == "77:01:0001001:1"
        assert isinstance(data["latitude"], float)
        assert isinstance(data["longitude"], float)

    def test_get_nonexistent_building(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting building with non-existent ID."""
        response = client.get("/api/v1/buildings/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestBuildingValidation:
    """Tests for building data validation."""

    def test_empty_result(
        self, client: TestClient, auth_headers: dict, sample_buildings: list[Building]
    ):
        """Test response when no buildings match filters."""
        response = client.get(
            "/api/v1/buildings?address=НесуществующийАдрес",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_response_structure(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test that response has correct structure."""
        response = client.get("/api/v1/buildings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        for building in data:
            assert "id" in building
            assert "address" in building
            assert "postcode" in building
            assert "cadastral_number" in building
            assert "latitude" in building
            assert "longitude" in building
            assert isinstance(building["latitude"], float)
            assert isinstance(building["longitude"], float)

    def test_coordinates_precision(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test that coordinates maintain precision."""
        building_id = sample_buildings[0].id
        response = client.get(f"/api/v1/buildings/{building_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Check that coordinates are preserved with good precision
        assert abs(data["latitude"] - 55.7558) < 0.0001
        assert abs(data["longitude"] - 37.6173) < 0.0001
