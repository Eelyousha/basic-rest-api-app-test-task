from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import verify_api_key
from app.models.models import Building
from app.schemas.schemas import BuildingSchema

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get("", response_model=List[BuildingSchema])
async def get_buildings(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get all buildings."""
    buildings = db.query(Building).all()
    return buildings
