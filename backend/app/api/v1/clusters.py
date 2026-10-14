from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.rbac import Role, get_current_user, require_roles
from app.db.database import get_database
from app.schemas.user import UserInDB
from app.services.cluster_service import list_clusters

router = APIRouter(prefix="/clusters", tags=["Clusters"])


@router.get("")
async def get_clusters(current_user: UserInDB = Depends(require_roles(Role.OFFICER, Role.DEPT_ADMIN, Role.ADMIN))):
    dept_id = current_user.department_id if current_user.role in ("officer", "dept_admin") else None
    return {"items": await list_clusters(department_id=dept_id)}


class ClusterStatusUpdate(BaseModel):
    status: str


@router.patch("/{cluster_id}/status")
async def update_cluster_status(
    cluster_id: str,
    body: ClusterStatusUpdate,
    _=Depends(require_roles(Role.DEPT_ADMIN, Role.ADMIN)),
):
    db = get_database()
    from bson import ObjectId
    from datetime import datetime, timezone

    result = await db.clusters.update_one(
        {"_id": ObjectId(cluster_id)},
        {"$set": {"status": body.status, "updated_at": datetime.now(timezone.utc)}},
    )
    if result.matched_count == 0:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Cluster not found")
    return {"id": cluster_id, "status": body.status}
