from typing import List, Optional
from pydantic import BaseModel, Field


# Building Schemas
class BuildingBase(BaseModel):
    address: str
    latitude: float
    longitude: float


class BuildingCreate(BuildingBase):
    pass


class BuildingSchema(BuildingBase):
    id: int

    class Config:
        from_attributes = True


# Activity Schemas
class ActivityBase(BaseModel):
    name: str
    parent_id: Optional[int] = None


class ActivityCreate(ActivityBase):
    pass


class ActivitySchema(ActivityBase):
    id: int
    level: int

    class Config:
        from_attributes = True


class ActivityTreeSchema(ActivitySchema):
    children: List['ActivityTreeSchema'] = []

    class Config:
        from_attributes = True


# Organization Schemas
class OrganizationBase(BaseModel):
    name: str
    building_id: int
    phones: Optional[List[str]] = []


class OrganizationCreate(OrganizationBase):
    activity_ids: List[int] = []


class OrganizationSchema(BaseModel):
    id: int
    name: str
    building_id: int
    phones: Optional[List[str]] = []

    class Config:
        from_attributes = True


class OrganizationDetailSchema(OrganizationSchema):
    building: BuildingSchema
    activities: List[ActivitySchema] = []

    class Config:
        from_attributes = True
