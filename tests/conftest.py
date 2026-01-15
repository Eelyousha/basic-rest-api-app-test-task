"""Pytest configuration and fixtures."""
import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.models.models import Activity, Building, Organization

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_headers() -> dict:
    """Return authentication headers with valid API key."""
    return {"X-API-Key": settings.API_KEY}


@pytest.fixture(scope="function")
def sample_buildings(db: Session) -> list[Building]:
    """Create sample buildings for testing."""
    buildings = [
        Building(
            address="Москва, ул. Ленина, 1",
            postcode="101000",
            cadastral_number="77:01:0001001:1",
            latitude=55.7558,
            longitude=37.6173,
        ),
        Building(
            address="Москва, ул. Пушкина, 10",
            postcode="102000",
            cadastral_number="77:01:0002001:1",
            latitude=55.7600,
            longitude=37.6200,
        ),
        Building(
            address="Санкт-Петербург, Невский пр., 1",
            postcode="190000",
            cadastral_number="78:01:0001001:1",
            latitude=59.9343,
            longitude=30.3351,
        ),
    ]
    for building in buildings:
        db.add(building)
    db.commit()
    for building in buildings:
        db.refresh(building)
    return buildings


@pytest.fixture(scope="function")
def sample_activities(db: Session) -> list[Activity]:
    """Create sample hierarchical activities for testing."""
    # Level 1
    food = Activity(name="Продукты питания", level=1)
    db.add(food)
    db.commit()
    db.refresh(food)

    # Level 2
    meat = Activity(name="Мясная продукция", parent_id=food.id, level=2)
    dairy = Activity(name="Молочная продукция", parent_id=food.id, level=2)
    db.add_all([meat, dairy])
    db.commit()
    db.refresh(meat)
    db.refresh(dairy)

    # Level 3
    beef = Activity(name="Говядина", parent_id=meat.id, level=3)
    pork = Activity(name="Свинина", parent_id=meat.id, level=3)
    db.add_all([beef, pork])
    db.commit()
    db.refresh(beef)
    db.refresh(pork)

    return [food, meat, dairy, beef, pork]


@pytest.fixture(scope="function")
def sample_organizations(
    db: Session, sample_buildings: list[Building], sample_activities: list[Activity]
) -> list[Organization]:
    """Create sample organizations for testing."""
    org1 = Organization(
        name='ООО "Рога и Копыта"',
        building_id=sample_buildings[0].id,
        phones=["+7-495-123-45-67", "+7-495-765-43-21"],
    )
    org1.activities.extend([sample_activities[1], sample_activities[3]])  # meat, beef

    org2 = Organization(
        name='ИП "Молочный рай"',
        building_id=sample_buildings[1].id,
        phones=["+7-495-111-22-33"],
    )
    org2.activities.append(sample_activities[2])  # dairy

    org3 = Organization(
        name='АО "Универсал"',
        building_id=sample_buildings[0].id,
        phones=["+7-495-999-88-77"],
    )
    org3.activities.extend(sample_activities[:3])  # food, meat, dairy

    db.add_all([org1, org2, org3])
    db.commit()
    for org in [org1, org2, org3]:
        db.refresh(org)

    return [org1, org2, org3]
