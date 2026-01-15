"""
Seed script to populate the database with test data.
Run after migrations: python scripts/seed_data.py
"""
import sys
import os

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.models.models import Building, Activity, Organization, Base


def seed_database():
    db = SessionLocal()

    try:
        print("Clearing existing data...")
        db.query(Organization).delete()
        db.query(Activity).delete()
        db.query(Building).delete()
        db.commit()

        print("Creating buildings...")
        buildings = [
            Building(
                address="Moscow, Lenin St. 1, office 3",
                latitude=55.7558,
                longitude=37.6173
            ),
            Building(
                address="Moscow, Blukhera St. 32/1",
                latitude=55.7500,
                longitude=37.6000
            ),
            Building(
                address="Moscow, Red Square 1",
                latitude=55.7539,
                longitude=37.6208
            )
        ]
        db.add_all(buildings)
        db.commit()
        print(f"Created {len(buildings)} buildings")

        print("Creating activities hierarchy...")
        # Level 1 activities
        food = Activity(name="Food", parent_id=None, level=1)
        automobiles = Activity(name="Automobiles", parent_id=None, level=1)
        db.add_all([food, automobiles])
        db.commit()

        # Level 2 activities
        meat_products = Activity(name="Meat Products", parent_id=food.id, level=2)
        dairy_products = Activity(name="Dairy Products", parent_id=food.id, level=2)
        trucks = Activity(name="Trucks", parent_id=automobiles.id, level=2)
        cars = Activity(name="Cars", parent_id=automobiles.id, level=2)
        db.add_all([meat_products, dairy_products, trucks, cars])
        db.commit()

        # Level 3 activities
        parts = Activity(name="Parts", parent_id=cars.id, level=3)
        accessories = Activity(name="Accessories", parent_id=cars.id, level=3)
        db.add_all([parts, accessories])
        db.commit()
        print(f"Created activity hierarchy with {db.query(Activity).count()} activities")

        print("Creating organizations...")
        organizations = [
            Organization(
                name="LLC Horns and Hooves",
                building_id=buildings[1].id,
                phones=["2-222-222", "3-333-333", "8-923-666-13-13"],
                activities=[dairy_products, meat_products]
            ),
            Organization(
                name="Meat Trading Co",
                building_id=buildings[0].id,
                phones=["1-111-111"],
                activities=[meat_products]
            ),
            Organization(
                name="Auto Parts Store",
                building_id=buildings[2].id,
                phones=["5-555-555", "6-666-666"],
                activities=[parts, accessories]
            ),
            Organization(
                name="Universal Motors",
                building_id=buildings[0].id,
                phones=["7-777-777"],
                activities=[trucks, cars]
            ),
            Organization(
                name="Fresh Dairy",
                building_id=buildings[1].id,
                phones=["4-444-444"],
                activities=[dairy_products]
            )
        ]
        db.add_all(organizations)
        db.commit()
        print(f"Created {len(organizations)} organizations")

        print("\n=== Seed data summary ===")
        print(f"Buildings: {db.query(Building).count()}")
        print(f"Activities: {db.query(Activity).count()}")
        print(f"Organizations: {db.query(Organization).count()}")
        print("\nActivity Tree:")
        for activity in db.query(Activity).filter(Activity.parent_id == None).all():
            print(f"  - {activity.name} (id={activity.id}, level={activity.level})")
            for child in activity.children:
                print(f"    - {child.name} (id={child.id}, level={child.level})")
                for grandchild in child.children:
                    print(f"      - {grandchild.name} (id={grandchild.id}, level={grandchild.level})")

        print("\n✓ Database seeded successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Starting database seed...")
    seed_database()
