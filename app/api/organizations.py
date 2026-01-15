from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.auth import verify_api_key
from app.core.geo_utils import haversine_distance, is_in_bounding_box
from app.models.models import Organization, Building, Activity
from app.schemas.schemas import OrganizationSchema, OrganizationDetailSchema

router = APIRouter(prefix="/organizations", tags=["organizations"])


def get_activity_with_descendants(db: Session, activity_id: int) -> List[int]:
    """Get an activity and all its descendant activity IDs."""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        return []
    return activity.get_all_descendants()


@router.get("", response_model=List[OrganizationSchema])
async def get_organizations(
    building_id: Optional[int] = Query(None, description="Filter by building ID"),
    activity_id: Optional[int] = Query(None, description="Filter by activity (includes children)"),
    name: Optional[str] = Query(None, description="Search by name (partial match)"),
    lat: Optional[float] = Query(None, description="Latitude for radius search"),
    lon: Optional[float] = Query(None, description="Longitude for radius search"),
    radius: Optional[float] = Query(None, description="Radius in meters"),
    lat_min: Optional[float] = Query(None, description="Min latitude for bounding box"),
    lat_max: Optional[float] = Query(None, description="Max latitude for bounding box"),
    lon_min: Optional[float] = Query(None, description="Min longitude for bounding box"),
    lon_max: Optional[float] = Query(None, description="Max longitude for bounding box"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get organizations with optional filtering:
    - building_id: Filter by building
    - activity_id: Filter by activity (includes all child activities)
    - name: Partial text search
    - lat, lon, radius: Geo radius search
    - lat_min, lat_max, lon_min, lon_max: Geo bounding box search
    """
    query = db.query(Organization).join(Building)

    if building_id is not None:
        query = query.filter(Organization.building_id == building_id)

    if activity_id is not None:
        activity_ids = get_activity_with_descendants(db, activity_id)
        if activity_ids:
            query = query.filter(Organization.activities.any(Activity.id.in_(activity_ids)))

    if name:
        query = query.filter(Organization.name.ilike(f"%{name}%"))

    organizations = query.all()

    # Apply geo filters if provided
    if lat is not None and lon is not None and radius is not None:
        filtered_orgs = []
        for org in organizations:
            distance = haversine_distance(lat, lon, org.building.latitude, org.building.longitude)
            if distance <= radius:
                filtered_orgs.append(org)
        organizations = filtered_orgs

    if lat_min is not None and lat_max is not None and lon_min is not None and lon_max is not None:
        organizations = [
            org for org in organizations
            if is_in_bounding_box(
                org.building.latitude, org.building.longitude,
                lat_min, lat_max, lon_min, lon_max
            )
        ]

    return organizations


@router.get("/{organization_id}", response_model=OrganizationDetailSchema)
async def get_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get detailed information about a specific organization."""
    organization = db.query(Organization).options(
        joinedload(Organization.building),
        joinedload(Organization.activities)
    ).filter(Organization.id == organization_id).first()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    return organization
