"""Tests for organization endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.models import Activity, Building, Organization


class TestOrganizationsList:
    """Tests for GET /api/v1/organizations endpoint."""

    def test_get_all_organizations(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
    ):
        """Test getting all organizations."""
        response = client.get("/api/v1/organizations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(org["name"] for org in data)
        assert all(org["building"] for org in data)

    def test_filter_by_building(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
        sample_buildings: list[Building],
    ):
        """Test filtering organizations by building_id."""
        building_id = sample_buildings[0].id
        response = client.get(
            f"/api/v1/organizations?building_id={building_id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # org1 and org3 are in building 0
        assert all(org["building"]["id"] == building_id for org in data)

    def test_filter_by_name(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
    ):
        """Test filtering organizations by name substring."""
        response = client.get('/api/v1/organizations?name=Рога', headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Рога и Копыта" in data[0]["name"]

    def test_filter_by_activity_parent(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
        sample_activities: list[Activity],
    ):
        """Test hierarchical activity search - searching by parent returns descendants."""
        food_id = sample_activities[0].id  # "Продукты питания" (parent)
        response = client.get(
            f"/api/v1/organizations?activity_id={food_id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # All 3 organizations have activities under "Продукты питания"
        assert len(data) == 3

    def test_filter_by_activity_child(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
        sample_activities: list[Activity],
    ):
        """Test filtering by specific child activity."""
        beef_id = sample_activities[3].id  # "Говядина" (child)
        response = client.get(
            f"/api/v1/organizations?activity_id={beef_id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Only org1 has "Говядина"
        assert len(data) == 1
        assert "Рога и Копыта" in data[0]["name"]

    def test_geo_search_radius(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
        sample_buildings: list[Building],
    ):
        """Test geo-search by radius."""
        # Search near building[0]: lat=55.7558, lon=37.6173
        # building[1] is very close (lat=55.7600, lon=37.6200) ~500m
        # building[2] is in St. Petersburg, very far away
        response = client.get(
            "/api/v1/organizations?lat=55.7558&lon=37.6173&radius=1000",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # All 3 orgs in Moscow buildings (0 and 1)

        # Smaller radius - only building[0]
        response = client.get(
            "/api/v1/organizations?lat=55.7558&lon=37.6173&radius=100",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Only orgs in building[0]

    def test_geo_search_bounding_box(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
    ):
        """Test geo-search by bounding box."""
        # Box around Moscow only
        response = client.get(
            "/api/v1/organizations?lat_min=55.7&lat_max=55.8&lon_min=37.5&lon_max=37.7",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # All 3 orgs are in Moscow

        # Box that excludes everything
        response = client.get(
            "/api/v1/organizations?lat_min=50.0&lat_max=50.1&lon_min=30.0&lon_max=30.1",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_combined_filters(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
        sample_buildings: list[Building],
        sample_activities: list[Activity],
    ):
        """Test combining multiple filters."""
        building_id = sample_buildings[0].id
        meat_id = sample_activities[1].id  # "Мясная продукция"
        response = client.get(
            f"/api/v1/organizations?building_id={building_id}&activity_id={meat_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # org1 and org3 in building[0] with meat activities


class TestOrganizationDetail:
    """Tests for GET /api/v1/organizations/{id} endpoint."""

    def test_get_organization_by_id(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
    ):
        """Test getting organization by ID."""
        org_id = sample_organizations[0].id
        response = client.get(f"/api/v1/organizations/{org_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == org_id
        assert "Рога и Копыта" in data["name"]
        assert data["building"] is not None
        assert len(data["activities"]) > 0
        assert len(data["phones"]) == 2

    def test_get_nonexistent_organization(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting organization with non-existent ID."""
        response = client.get("/api/v1/organizations/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestOrganizationValidation:
    """Tests for organization data validation."""

    def test_empty_result(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test response when no organizations match filters."""
        response = client.get(
            "/api/v1/organizations?name=НесуществующаяОрганизация",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_geo_search_validation(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
    ):
        """Test that geo-search requires complete parameters."""
        # Radius search requires lat, lon, and radius
        response = client.get(
            "/api/v1/organizations?lat=55.7558&lon=37.6173", headers=auth_headers
        )
        assert response.status_code == 200  # Should work, just no geo-filtering

        # Bounding box requires all 4 parameters
        response = client.get(
            "/api/v1/organizations?lat_min=55.7&lat_max=55.8", headers=auth_headers
        )
        assert response.status_code == 200  # Should work, just no geo-filtering

    def test_response_structure(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
    ):
        """Test that response has correct structure."""
        response = client.get("/api/v1/organizations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        for org in data:
            assert "id" in org
            assert "name" in org
            assert "phones" in org
            assert isinstance(org["phones"], list)
            assert "building" in org
            assert "activities" in org
            assert isinstance(org["activities"], list)

            # Check building structure
            building = org["building"]
            assert "id" in building
            assert "address" in building
            assert "latitude" in building
            assert "longitude" in building

            # Check activities structure
            for activity in org["activities"]:
                assert "id" in activity
                assert "name" in activity
                assert "level" in activity
