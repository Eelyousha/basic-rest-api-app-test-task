from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import verify_api_key
from app.models.models import Activity
from app.schemas.schemas import ActivitySchema, ActivityTreeSchema

router = APIRouter(prefix="/activities", tags=["activities"])


def build_activity_tree(activities: List[Activity]) -> List[ActivityTreeSchema]:
    """Build a hierarchical tree structure from flat activity list."""
    activity_map = {activity.id: ActivityTreeSchema.from_orm(activity) for activity in activities}

    for activity in activity_map.values():
        activity.children = []

    root_activities = []
    for activity in activities:
        activity_schema = activity_map[activity.id]
        if activity.parent_id is None:
            root_activities.append(activity_schema)
        else:
            if activity.parent_id in activity_map:
                activity_map[activity.parent_id].children.append(activity_schema)

    return root_activities


@router.get("", response_model=List[ActivitySchema] | List[ActivityTreeSchema])
async def get_activities(
    include_tree: Optional[bool] = Query(False, description="Return nested tree structure"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get all activities.
    - include_tree=false: Returns flat list
    - include_tree=true: Returns hierarchical tree structure
    """
    activities = db.query(Activity).all()

    if include_tree:
        return build_activity_tree(activities)

    return activities
