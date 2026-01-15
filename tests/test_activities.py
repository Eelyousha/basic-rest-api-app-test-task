"""Tests for activity endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.models import Activity


class TestActivitiesList:
    """Tests for GET /api/v1/activities endpoint."""

    def test_get_all_activities(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_activities: list[Activity],
    ):
        """Test getting all activities."""
        response = client.get("/api/v1/activities", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        assert all(activity["name"] for activity in data)
        assert all(activity["level"] in [1, 2, 3] for activity in data)

    def test_filter_by_name(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_activities: list[Activity],
    ):
        """Test filtering activities by name substring."""
        response = client.get(
            "/api/v1/activities?name=Мясная", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Мясная продукция" == data[0]["name"]

        response = client.get(
            "/api/v1/activities?name=продукция", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # "Мясная продукция" and "Молочная продукция"

    def test_filter_by_parent_id(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_activities: list[Activity],
    ):
        """Test filtering activities by parent_id."""
        food_id = sample_activities[0].id
        response = client.get(
            f"/api/v1/activities?parent_id={food_id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # "Мясная" and "Молочная"
        assert all(activity["parent_id"] == food_id for activity in data)

        meat_id = sample_activities[1].id
        response = client.get(
            f"/api/v1/activities?parent_id={meat_id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # "Говядина" and "Свинина"

    def test_filter_by_level(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_activities: list[Activity],
    ):
        """Test filtering activities by level."""
        response = client.get("/api/v1/activities?level=1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["level"] == 1

        response = client.get("/api/v1/activities?level=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        response = client.get("/api/v1/activities?level=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_root_activities(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_activities: list[Activity],
    ):
        """Test getting root-level activities (parent_id is null)."""
        response = client.get("/api/v1/activities?level=1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        for activity in data:
            assert activity["parent_id"] is None

    def test_combined_filters(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_activities: list[Activity],
    ):
        """Test combining multiple filters."""
        meat_id = sample_activities[1].id
        response = client.get(
            f"/api/v1/activities?parent_id={meat_id}&level=3",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Both beef and pork are level 3 children of meat


class TestActivityDetail:
    """Tests for GET /api/v1/activities/{id} endpoint."""

    def test_get_activity_by_id(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_activities: list[Activity],
    ):
        """Test getting activity by ID."""
        activity_id = sample_activities[0].id
        response = client.get(f"/api/v1/activities/{activity_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == activity_id
        assert data["name"] == "Продукты питания"
        assert data["level"] == 1
        assert data["parent_id"] is None

    def test_get_child_activity(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_activities: list[Activity],
    ):
        """Test getting child activity with parent reference."""
        meat_id = sample_activities[1].id
        response = client.get(f"/api/v1/activities/{meat_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Мясная продукция"
        assert data["level"] == 2
        assert data["parent_id"] == sample_activities[0].id

    def test_get_nonexistent_activity(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting activity with non-existent ID."""
        response = client.get("/api/v1/activities/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestActivityHierarchy:
    """Tests for activity hierarchical structure."""

    def test_three_level_hierarchy(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_activities: list[Activity],
    ):
        """Test that hierarchy has correct structure."""
        # Level 1
        response = client.get("/api/v1/activities?level=1", headers=auth_headers)
        level1 = response.json()
        assert len(level1) == 1
        assert level1[0]["parent_id"] is None

        # Level 2
        response = client.get("/api/v1/activities?level=2", headers=auth_headers)
        level2 = response.json()
        assert len(level2) == 2
        assert all(act["parent_id"] == level1[0]["id"] for act in level2)

        # Level 3
        response = client.get("/api/v1/activities?level=3", headers=auth_headers)
        level3 = response.json()
        assert len(level3) == 2
        level2_ids = [act["id"] for act in level2]
        assert all(act["parent_id"] in level2_ids for act in level3)

    def test_max_three_levels(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_activities: list[Activity],
    ):
        """Test that no activities exist beyond level 3."""
        response = client.get("/api/v1/activities?level=4", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

        # Verify all activities are between 1 and 3
        response = client.get("/api/v1/activities", headers=auth_headers)
        data = response.json()
        assert all(1 <= activity["level"] <= 3 for activity in data)

    def test_parent_child_relationship(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_activities: list[Activity],
    ):
        """Test parent-child relationships are consistent."""
        food_id = sample_activities[0].id
        meat_id = sample_activities[1].id
        beef_id = sample_activities[3].id

        # Get meat activity
        response = client.get(f"/api/v1/activities/{meat_id}", headers=auth_headers)
        meat = response.json()
        assert meat["parent_id"] == food_id

        # Get beef activity
        response = client.get(f"/api/v1/activities/{beef_id}", headers=auth_headers)
        beef = response.json()
        assert beef["parent_id"] == meat_id

        # Beef's grandparent should be food
        # (This is implicit through the chain: beef -> meat -> food)


class TestActivityValidation:
    """Tests for activity data validation."""

    def test_empty_result(
        self, client: TestClient, auth_headers: dict, sample_activities: list[Activity]
    ):
        """Test response when no activities match filters."""
        response = client.get(
            "/api/v1/activities?name=НесуществующаяДеятельность",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_response_structure(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_activities: list[Activity],
    ):
        """Test that response has correct structure."""
        response = client.get("/api/v1/activities", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        for activity in data:
            assert "id" in activity
            assert "name" in activity
            assert "level" in activity
            assert "parent_id" in activity  # Can be null
            assert isinstance(activity["id"], int)
            assert isinstance(activity["name"], str)
            assert isinstance(activity["level"], int)
            assert activity["parent_id"] is None or isinstance(activity["parent_id"], int)

    def test_unique_names(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_activities: list[Activity],
    ):
        """Test that all activity names are unique."""
        response = client.get("/api/v1/activities", headers=auth_headers)
        data = response.json()
        names = [activity["name"] for activity in data]
        assert len(names) == len(set(names))  # No duplicates
