from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableList

from app.core.database import Base

# Association table for many-to-many relationship between Organization and Activity
organization_activity = Table(
    'organization_activity',
    Base.metadata,
    Column('organization_id', Integer, ForeignKey('organizations.id', ondelete='CASCADE'), primary_key=True),
    Column('activity_id', Integer, ForeignKey('activities.id', ondelete='CASCADE'), primary_key=True)
)


class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, nullable=False)
    postcode = Column(String, nullable=True)
    cadastral_number = Column(String, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    organizations = relationship("Organization", back_populates="building")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    parent_id = Column(Integer, ForeignKey('activities.id', ondelete='CASCADE'), nullable=True)
    level = Column(Integer, nullable=False, default=1)

    parent = relationship("Activity", remote_side=[id], backref="children")
    organizations = relationship("Organization", secondary=organization_activity, back_populates="activities")

    def get_all_descendants(self):
        """Recursively get all descendant activity IDs"""
        descendants = [self.id]
        for child in self.children:
            descendants.extend(child.get_all_descendants())
        return descendants


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    building_id = Column(Integer, ForeignKey('buildings.id', ondelete='CASCADE'), nullable=False)
    # Use ARRAY for PostgreSQL, JSON for SQLite (testing)
    phones = Column(ARRAY(String).with_variant(JSON, "sqlite"), nullable=True)

    building = relationship("Building", back_populates="organizations")
    activities = relationship("Activity", secondary=organization_activity, back_populates="organizations")
