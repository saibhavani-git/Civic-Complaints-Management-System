from fastapi import APIRouter, Depends, HTTPException, status

from app.core.rbac import Role, require_roles
from app.schemas.staff import AssignOfficerRequest, DeptWorkerCreate
from app.schemas.user import UserInDB, UserResponse
from app.services.auth_service import create_staff_user
from app.services.complaint_service import assign_complaint_officer, list_department_officers

router = APIRouter(prefix="/staff", tags=["Staff"])


@router.get("/officers")
async def get_officers(
    department_id: str | None = None,
    current_user: UserInDB = Depends(require_roles(Role.DEPT_ADMIN, Role.ADMIN)),
):
    dept = department_id
    if current_user.role == Role.DEPT_ADMIN.value:
        dept = current_user.department_id
    if not dept:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="department_id required")
    return await list_department_officers(dept)


@router.get("/team")
async def list_department_team(
    current_user: UserInDB = Depends(require_roles(Role.DEPT_ADMIN)),
):
    if not current_user.department_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No department on your account")
    return await list_department_officers(current_user.department_id)


@router.post("/team", response_model=UserResponse, status_code=201)
async def add_department_worker(
    data: DeptWorkerCreate,
    current_user: UserInDB = Depends(require_roles(Role.DEPT_ADMIN)),
):
    if not current_user.department_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No department on your account")
    return await create_staff_user(
        email=data.email,
        password=data.password,
        full_name=data.full_name,
        phone=data.phone,
        role=Role.OFFICER.value,
        department_id=current_user.department_id,
        service_area=data.service_area,
    )


@router.post("/complaints/{complaint_id}/assign")
async def assign_officer(
    complaint_id: str,
    body: AssignOfficerRequest,
    current_user: UserInDB = Depends(require_roles(Role.DEPT_ADMIN, Role.ADMIN)),
):
    return await assign_complaint_officer(
        complaint_id,
        body.officer_id,
        current_user.id,
        current_user.role,
        current_user.department_id,
    )
