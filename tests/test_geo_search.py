"""Tests for geo-search functionality."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.geo_utils import calculate_bounding_box, haversine_distance
from app.models.models import Building


class TestHaversineDistance:
    """Tests for Haversine distance calculation."""

    def test_distance_same_point(self):
        """Test distance between same point is zero."""
        distance = haversine_distance(55.7558, 37.6173, 55.7558, 37.6173)
        assert distance == 0.0

    def test_distance_moscow_spb(self):
        """Test distance between Moscow and St. Petersburg."""
        # Moscow: 55.7558, 37.6173
        # St. Petersburg: 59.9343, 30.3351
        distance = haversine_distance(55.7558, 37.6173, 59.9343, 30.3351)
        # Expected distance is approximately 634 km
        assert 630000 < distance < 640000

    def test_distance_symmetry(self):
        """Test that distance calculation is symmetric."""
        dist1 = haversine_distance(55.7558, 37.6173, 59.9343, 30.3351)
        dist2 = haversine_distance(59.9343, 30.3351, 55.7558, 37.6173)
        assert abs(dist1 - dist2) < 0.001  # Should be exactly equal

    def test_short_distance(self):
        """Test short distance calculation (within same city)."""
        # Two points in Moscow ~500m apart
        dist = haversine_distance(55.7558, 37.6173, 55.7600, 37.6200)
        # Expected ~500-600 meters
        assert 400 < dist < 700

    def test_equator_distance(self):
        """Test distance calculation on equator."""
        # 1 degree longitude at equator ≈ 111 km
        dist = haversine_distance(0, 0, 0, 1)
        assert 110000 < dist < 112000


class TestBoundingBox:
    """Tests for bounding box calculation."""

    def test_bounding_box_creation(self):
        """Test creating bounding box from center and radius."""
        lat, lon, radius = 55.7558, 37.6173, 1000  # 1km radius
        bbox = calculate_bounding_box(lat, lon, radius)

        assert "lat_min" in bbox
        assert "lat_max" in bbox
        assert "lon_min" in bbox
        assert "lon_max" in bbox

        # Bounding box should be centered around the point
        assert bbox["lat_min"] < lat < bbox["lat_max"]
        assert bbox["lon_min"] < lon < bbox["lon_max"]

    def test_bounding_box_symmetry(self):
        """Test that bounding box is roughly symmetric around center."""
        lat, lon, radius = 55.7558, 37.6173, 1000
        bbox = calculate_bounding_box(lat, lon, radius)

        lat_delta = bbox["lat_max"] - bbox["lat_min"]
        lon_delta = bbox["lon_max"] - bbox["lon_min"]

        # At high latitudes, longitude delta should be larger than latitude delta
        # (due to projection effects)
        assert lat_delta > 0
        assert lon_delta > 0

    def test_different_radii(self):
        """Test bounding boxes with different radii."""
        lat, lon = 55.7558, 37.6173
        bbox_small = calculate_bounding_box(lat, lon, 500)
        bbox_large = calculate_bounding_box(lat, lon, 5000)

        # Larger radius should produce larger bounding box
        assert bbox_large["lat_max"] > bbox_small["lat_max"]
        assert bbox_large["lat_min"] < bbox_small["lat_min"]
        assert bbox_large["lon_max"] > bbox_small["lon_max"]
        assert bbox_large["lon_min"] < bbox_small["lon_min"]


class TestGeoSearchBuildings:
    """Tests for geo-search on buildings."""

    def test_radius_search_all_within(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test radius search that includes all buildings."""
        # Search from Moscow with very large radius
        response = client.get(
            "/api/v1/buildings?lat=55.7558&lon=37.6173&radius=1000000",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # All buildings

    def test_radius_search_none_within(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test radius search with no buildings within range."""
        # Search from middle of nowhere with small radius
        response = client.get(
            "/api/v1/buildings?lat=0.0&lon=0.0&radius=1000",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_radius_search_progressive(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test that increasing radius includes more buildings."""
        center_lat, center_lon = 55.7558, 37.6173

        # Very small radius
        response = client.get(
            f"/api/v1/buildings?lat={center_lat}&lon={center_lon}&radius=10",
            headers=auth_headers,
        )
        count_10m = len(response.json())

        # Medium radius
        response = client.get(
            f"/api/v1/buildings?lat={center_lat}&lon={center_lon}&radius=1000",
            headers=auth_headers,
        )
        count_1km = len(response.json())

        # Large radius
        response = client.get(
            f"/api/v1/buildings?lat={center_lat}&lon={center_lon}&radius=10000",
            headers=auth_headers,
        )
        count_10km = len(response.json())

        # Each larger radius should include at least as many results
        assert count_10m <= count_1km <= count_10km

    def test_bounding_box_moscow_only(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test bounding box that includes only Moscow buildings."""
        response = client.get(
            "/api/v1/buildings?lat_min=55.7&lat_max=55.8&lon_min=37.5&lon_max=37.7",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Two Moscow buildings
        assert all("Москва" in b["address"] for b in data)

    def test_bounding_box_spb_only(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test bounding box that includes only St. Petersburg buildings."""
        response = client.get(
            "/api/v1/buildings?lat_min=59.9&lat_max=60.0&lon_min=30.3&lon_max=30.4",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Санкт-Петербург" in data[0]["address"]

    def test_bounding_box_empty(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test bounding box with no buildings inside."""
        response = client.get(
            "/api/v1/buildings?lat_min=0.0&lat_max=1.0&lon_min=0.0&lon_max=1.0",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestGeoSearchOrganizations:
    """Tests for geo-search on organizations (through buildings)."""

    def test_organizations_radius_search(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations,
        sample_buildings: list[Building],
    ):
        """Test radius search for organizations."""
        # Search near first Moscow building
        response = client.get(
            "/api/v1/organizations?lat=55.7558&lon=37.6173&radius=1000",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        # All returned orgs should be in buildings within radius

    def test_organizations_bounding_box(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations,
    ):
        """Test bounding box search for organizations."""
        response = client.get(
            "/api/v1/organizations?lat_min=55.7&lat_max=55.8&lon_min=37.5&lon_max=37.7",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # All orgs are in Moscow buildings

    def test_combined_geo_and_activity_filter(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations,
        sample_activities,
    ):
        """Test combining geo-search with activity filter."""
        meat_id = sample_activities[1].id  # "Мясная продукция"
        response = client.get(
            f"/api/v1/organizations?lat=55.7558&lon=37.6173&radius=1000&activity_id={meat_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # Should return orgs with meat activities in Moscow
        assert len(data) > 0


class TestGeoSearchEdgeCases:
    """Tests for edge cases in geo-search."""

    def test_radius_zero(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test radius search with zero radius."""
        response = client.get(
            "/api/v1/buildings?lat=55.7558&lon=37.6173&radius=0",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # Zero radius should match nothing (or only exact coordinates)
        assert len(data) == 0

    def test_negative_radius(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test that negative radius is handled."""
        response = client.get(
            "/api/v1/buildings?lat=55.7558&lon=37.6173&radius=-100",
            headers=auth_headers,
        )
        # Should either return 422 (validation error) or treat as no filter
        assert response.status_code in [200, 422]

    def test_inverted_bounding_box(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test bounding box with min > max."""
        response = client.get(
            "/api/v1/buildings?lat_min=60.0&lat_max=55.0&lon_min=40.0&lon_max=30.0",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # Inverted box should match nothing
        assert len(data) == 0

    def test_extreme_coordinates(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test with extreme latitude/longitude values."""
        # North Pole
        response = client.get(
            "/api/v1/buildings?lat=90.0&lon=0.0&radius=1000000",
            headers=auth_headers,
        )
        assert response.status_code == 200

        # South Pole
        response = client.get(
            "/api/v1/buildings?lat=-90.0&lon=0.0&radius=1000000",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_partial_geo_params_radius(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test that incomplete radius params don't cause errors."""
        # Only lat and lon, no radius - should return all buildings
        response = client.get(
            "/api/v1/buildings?lat=55.7558&lon=37.6173",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # No filtering applied

    def test_partial_geo_params_bbox(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
    ):
        """Test that incomplete bbox params don't cause errors."""
        # Only lat_min and lat_max, no lon params
        response = client.get(
            "/api/v1/buildings?lat_min=55.7&lat_max=55.8",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # No filtering applied
