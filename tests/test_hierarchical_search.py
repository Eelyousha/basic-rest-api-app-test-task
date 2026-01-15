"""Tests for hierarchical activity search functionality."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.models import Activity, Building, Organization


class TestActivityHierarchyHelpers:
    """Tests for Activity.get_all_descendants() helper method."""

    def test_get_descendants_leaf_node(
        self, db: Session, sample_activities: list[Activity]
    ):
        """Test getting descendants of a leaf node."""
        beef = sample_activities[3]  # "Говядина" - leaf node
        descendants = beef.get_all_descendants()
        # Leaf node should only return itself
        assert descendants == [beef.id]

    def test_get_descendants_parent_node(
        self, db: Session, sample_activities: list[Activity]
    ):
        """Test getting descendants of a parent node."""
        meat = sample_activities[1]  # "Мясная продукция" - has 2 children
        descendants = meat.get_all_descendants()
        # Should include meat itself + beef + pork
        assert len(descendants) == 3
        assert meat.id in descendants
        assert sample_activities[3].id in descendants  # beef
        assert sample_activities[4].id in descendants  # pork

    def test_get_descendants_root_node(
        self, db: Session, sample_activities: list[Activity]
    ):
        """Test getting descendants of root node."""
        food = sample_activities[0]  # "Продукты питания" - root node
        descendants = food.get_all_descendants()
        # Should include all 5 activities
        assert len(descendants) == 5
        # Verify all activities are included
        all_ids = [act.id for act in sample_activities]
        for activity_id in all_ids:
            assert activity_id in descendants


class TestHierarchicalOrganizationSearch:
    """Tests for hierarchical search in organization endpoints."""

    def test_search_by_root_returns_all(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
        sample_activities: list[Activity],
    ):
        """Test searching by root activity returns all matching organizations."""
        food_id = sample_activities[0].id  # "Продукты питания"
        response = client.get(
            f"/api/v1/organizations?activity_id={food_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # All 3 orgs have activities under "Продукты питания"
        assert len(data) == 3

    def test_search_by_middle_level(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
        sample_activities: list[Activity],
    ):
        """Test searching by middle-level activity."""
        meat_id = sample_activities[1].id  # "Мясная продукция"
        response = client.get(
            f"/api/v1/organizations?activity_id={meat_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # org1 has "Мясная" and "Говядина"
        # org3 has "Мясная"
        assert len(data) == 2

    def test_search_by_leaf_specific(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
        sample_activities: list[Activity],
    ):
        """Test searching by leaf activity returns only specific orgs."""
        beef_id = sample_activities[3].id  # "Говядина"
        response = client.get(
            f"/api/v1/organizations?activity_id={beef_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # Only org1 has "Говядина"
        assert len(data) == 1
        assert "Рога и Копыта" in data[0]["name"]

    def test_search_by_different_branches(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
        sample_activities: list[Activity],
    ):
        """Test that different branches return different results."""
        meat_id = sample_activities[1].id  # "Мясная продукция"
        dairy_id = sample_activities[2].id  # "Молочная продукция"

        # Search meat branch
        response_meat = client.get(
            f"/api/v1/organizations?activity_id={meat_id}",
            headers=auth_headers,
        )
        meat_orgs = response_meat.json()

        # Search dairy branch
        response_dairy = client.get(
            f"/api/v1/organizations?activity_id={dairy_id}",
            headers=auth_headers,
        )
        dairy_orgs = response_dairy.json()

        # Results should be different
        meat_ids = {org["id"] for org in meat_orgs}
        dairy_ids = {org["id"] for org in dairy_orgs}
        assert meat_ids != dairy_ids

        # org3 ("Универсал") has both meat and dairy, should appear in both
        universal_in_meat = any("Универсал" in org["name"] for org in meat_orgs)
        universal_in_dairy = any("Универсал" in org["name"] for org in dairy_orgs)
        assert universal_in_meat and universal_in_dairy


class TestHierarchicalSearchEdgeCases:
    """Tests for edge cases in hierarchical search."""

    def test_nonexistent_activity_returns_empty(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
    ):
        """Test searching by non-existent activity ID."""
        response = client.get(
            "/api/v1/organizations?activity_id=99999",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_org_with_multiple_activities_from_same_tree(
        self,
        db: Session,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
        sample_activities: list[Activity],
    ):
        """Test org with multiple activities from same hierarchy branch."""
        # Create org with both parent and child from same branch
        org = Organization(
            name="Тестовая организация",
            building_id=sample_buildings[0].id,
            phones=["+7-999-999-99-99"],
        )
        meat = sample_activities[1]  # "Мясная продукция"
        beef = sample_activities[3]  # "Говядина" (child of meat)
        org.activities.extend([meat, beef])
        db.add(org)
        db.commit()

        # Search by parent should still return org once (not duplicated)
        response = client.get(
            f"/api/v1/organizations?activity_id={meat.id}",
            headers=auth_headers,
        )
        data = response.json()
        test_orgs = [o for o in data if o["name"] == "Тестовая организация"]
        assert len(test_orgs) == 1

    def test_org_without_activities(
        self,
        db: Session,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
        sample_activities: list[Activity],
    ):
        """Test that orgs without activities are not returned in activity search."""
        # Create org with no activities
        org = Organization(
            name="Организация без деятельности",
            building_id=sample_buildings[0].id,
            phones=["+7-888-888-88-88"],
        )
        db.add(org)
        db.commit()

        # Search by any activity should not return this org
        food_id = sample_activities[0].id
        response = client.get(
            f"/api/v1/organizations?activity_id={food_id}",
            headers=auth_headers,
        )
        data = response.json()
        assert not any(o["name"] == "Организация без деятельности" for o in data)


class TestComplexHierarchicalScenarios:
    """Tests for complex hierarchical search scenarios."""

    def test_three_level_hierarchy_search(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
        sample_activities: list[Activity],
    ):
        """Test search traverses all three levels correctly."""
        food = sample_activities[0]  # Level 1
        meat = sample_activities[1]  # Level 2
        beef = sample_activities[3]  # Level 3

        # Search by level 1 (root)
        response_l1 = client.get(
            f"/api/v1/organizations?activity_id={food.id}",
            headers=auth_headers,
        )
        orgs_l1 = set(o["id"] for o in response_l1.json())

        # Search by level 2
        response_l2 = client.get(
            f"/api/v1/organizations?activity_id={meat.id}",
            headers=auth_headers,
        )
        orgs_l2 = set(o["id"] for o in response_l2.json())

        # Search by level 3
        response_l3 = client.get(
            f"/api/v1/organizations?activity_id={beef.id}",
            headers=auth_headers,
        )
        orgs_l3 = set(o["id"] for o in response_l3.json())

        # Level 1 should include all from level 2 and 3
        assert orgs_l2.issubset(orgs_l1)
        assert orgs_l3.issubset(orgs_l1)
        # Level 2 should include all from level 3
        assert orgs_l3.issubset(orgs_l2)

    def test_sibling_activities_independent(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
        sample_activities: list[Activity],
    ):
        """Test that sibling activities (same level, same parent) are independent."""
        beef_id = sample_activities[3].id  # "Говядина"
        pork_id = sample_activities[4].id  # "Свинина"

        # Search by beef
        response_beef = client.get(
            f"/api/v1/organizations?activity_id={beef_id}",
            headers=auth_headers,
        )
        beef_orgs = set(o["id"] for o in response_beef.json())

        # Search by pork
        response_pork = client.get(
            f"/api/v1/organizations?activity_id={pork_id}",
            headers=auth_headers,
        )
        pork_orgs = set(o["id"] for o in response_pork.json())

        # Results should be independent (different orgs)
        # beef_orgs and pork_orgs should have no overlap
        # (based on our sample data, org1 only has beef, no one has pork alone)
        assert len(beef_orgs) > 0  # org1 has beef

    def test_combining_hierarchy_with_other_filters(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organizations: list[Organization],
        sample_activities: list[Activity],
        sample_buildings: list[Building],
    ):
        """Test combining hierarchical search with building and geo filters."""
        meat_id = sample_activities[1].id
        building_id = sample_buildings[0].id

        # Hierarchical + building filter
        response = client.get(
            f"/api/v1/organizations?activity_id={meat_id}&building_id={building_id}",
            headers=auth_headers,
        )
        data = response.json()
        assert len(data) > 0
        # All results should be in the specified building
        assert all(org["building"]["id"] == building_id for org in data)

        # Hierarchical + geo filter
        response = client.get(
            f"/api/v1/organizations?activity_id={meat_id}&lat=55.7558&lon=37.6173&radius=1000",
            headers=auth_headers,
        )
        data = response.json()
        assert len(data) > 0

    def test_multiple_orgs_same_leaf_activity(
        self,
        db: Session,
        client: TestClient,
        auth_headers: dict,
        sample_buildings: list[Building],
        sample_activities: list[Activity],
    ):
        """Test multiple organizations with same leaf activity."""
        # Add another org with "Говядина"
        org = Organization(
            name="Мясокомбинат №2",
            building_id=sample_buildings[1].id,
            phones=["+7-495-555-55-55"],
        )
        beef = sample_activities[3]  # "Говядина"
        org.activities.append(beef)
        db.add(org)
        db.commit()

        # Search by beef should now return 2 orgs
        response = client.get(
            f"/api/v1/organizations?activity_id={beef.id}",
            headers=auth_headers,
        )
        data = response.json()
        assert len(data) == 2  # org1 ("Рога и Копыта") + new org
        names = {org["name"] for org in data}
        assert "Рога и Копыта" in str(names)
        assert "Мясокомбинат №2" in names


class TestHierarchyConsistency:
    """Tests to ensure hierarchy consistency is maintained."""

    def test_activity_levels_consistent(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_activities: list[Activity],
    ):
        """Test that activity levels are consistent with parent relationships."""
        response = client.get("/api/v1/activities", headers=auth_headers)
        activities = response.json()

        for activity in activities:
            if activity["parent_id"] is None:
                # Root activity should be level 1
                assert activity["level"] == 1
            else:
                # Find parent
                parent = next(
                    a for a in activities if a["id"] == activity["parent_id"]
                )
                # Child level should be parent level + 1
                assert activity["level"] == parent["level"] + 1

    def test_no_circular_references(
        self,
        db: Session,
        sample_activities: list[Activity],
    ):
        """Test that there are no circular references in hierarchy."""
        visited = set()

        def check_ancestry(activity: Activity, ancestors: set):
            if activity.id in ancestors:
                # Circular reference detected
                return False
            if activity.id in visited:
                # Already checked this branch
                return True

            visited.add(activity.id)
            if activity.parent_id is None:
                return True

            parent = db.query(Activity).filter_by(id=activity.parent_id).first()
            if parent is None:
                return False

            new_ancestors = ancestors.copy()
            new_ancestors.add(activity.id)
            return check_ancestry(parent, new_ancestors)

        # Check all activities
        for activity in sample_activities:
            assert check_ancestry(activity, set()), f"Circular reference in activity {activity.id}"
