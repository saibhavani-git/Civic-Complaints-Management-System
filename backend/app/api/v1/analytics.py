from bson import ObjectId
from fastapi import APIRouter, Depends

from app.core.rbac import Role, require_roles
from app.schemas.common import AnalyticsOverview
from app.schemas.user import UserInDB
from app.services.analytics_service import (
    get_analytics_overview,
    get_complaint_trends,
    get_complaints_by_department,
    get_heatmap_data,
    get_officer_workload,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _dept_scope(user: UserInDB) -> ObjectId | None:
    if user.role == Role.DEPT_ADMIN.value and user.department_id:
        return ObjectId(user.department_id)
    return None


@router.get("/overview", response_model=AnalyticsOverview)
async def overview(current_user: UserInDB = Depends(require_roles(Role.OFFICER, Role.DEPT_ADMIN, Role.ADMIN))):
    return await get_analytics_overview(department_id=_dept_scope(current_user))


@router.get("/by-department")
async def by_department(current_user: UserInDB = Depends(require_roles(Role.OFFICER, Role.DEPT_ADMIN, Role.ADMIN))):
    return await get_complaints_by_department(department_id=_dept_scope(current_user))


@router.get("/trends")
async def trends(current_user: UserInDB = Depends(require_roles(Role.DEPT_ADMIN, Role.ADMIN))):
    return await get_complaint_trends(department_id=_dept_scope(current_user))


@router.get("/heatmap")
async def heatmap(_=Depends(require_roles(Role.OFFICER, Role.ADMIN))):
    return await get_heatmap_data()


@router.get("/officer-workload")
async def officer_workload(_=Depends(require_roles(Role.ADMIN))):
    return await get_officer_workload()
