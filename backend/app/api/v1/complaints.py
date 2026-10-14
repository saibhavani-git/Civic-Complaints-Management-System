from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.rbac import Role, get_current_user, require_roles
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintListResponse,
    ComplaintResponse,
    ComplaintStatusUpdate,
    ResolutionSchema,
)
from app.schemas.common import FeedbackCreate
from app.schemas.user import UserInDB
from app.schemas.staff import AssignOfficerRequest
from app.services.complaint_service import (
    assign_complaint_officer,
    create_complaint,
    get_complaint_for_viewer,
    get_nearby_complaints,
    list_complaints,
    resolve_complaint,
    submit_feedback,
    update_complaint_status,
)

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post("", response_model=ComplaintResponse, status_code=201)
async def submit_complaint(
    title: str = Form(...),
    description: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    address: str = Form(...),
    images: list[UploadFile] = File(default=[]),
    current_user: UserInDB = Depends(require_roles(Role.CITIZEN)),
):
    data = ComplaintCreate(
        title=title,
        description=description,
        latitude=latitude,
        longitude=longitude,
        address=address,
    )
    return await create_complaint(data, current_user.id, images)


@router.get("", response_model=ComplaintListResponse)
async def get_complaints(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    awaiting_assignment: bool = False,
    current_user: UserInDB = Depends(get_current_user),
):
    role = current_user.role
    if hasattr(role, "value"):
        role = role.value
    result = await list_complaints(
        user_id=current_user.id,
        role=role,
        page=page,
        limit=min(limit, 100),
        status_filter=status,
        priority_filter=priority,
        awaiting_assignment=awaiting_assignment,
    )
    return ComplaintListResponse(**result)


@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(
    complaint_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    return await get_complaint_for_viewer(
        complaint_id,
        user_id=current_user.id,
        role=current_user.role,
        department_id=current_user.department_id,
    )


@router.get("/{complaint_id}/nearby")
async def nearby_complaints(
    complaint_id: str,
    radius: int = 500,
    current_user: UserInDB = Depends(require_roles(Role.OFFICER, Role.DEPT_ADMIN, Role.ADMIN)),
):
    return {"items": await get_nearby_complaints(complaint_id, radius)}


@router.post("/{complaint_id}/assign", response_model=ComplaintResponse)
async def assign_complaint(
    complaint_id: str,
    data: AssignOfficerRequest,
    current_user: UserInDB = Depends(require_roles(Role.DEPT_ADMIN, Role.ADMIN)),
):
    return await assign_complaint_officer(
        complaint_id,
        data.officer_id,
        current_user.id,
        current_user.role,
        current_user.department_id,
    )


@router.patch("/{complaint_id}/status", response_model=ComplaintResponse)
async def patch_status(
    complaint_id: str,
    data: ComplaintStatusUpdate,
    current_user: UserInDB = Depends(require_roles(Role.OFFICER, Role.DEPT_ADMIN, Role.ADMIN)),
):
    return await update_complaint_status(
        complaint_id, data.status.value, current_user.id, data.note
    )


@router.post("/{complaint_id}/resolve", response_model=ComplaintResponse)
async def post_resolve(
    complaint_id: str,
    data: ResolutionSchema,
    current_user: UserInDB = Depends(require_roles(Role.OFFICER, Role.DEPT_ADMIN, Role.ADMIN)),
):
    return await resolve_complaint(complaint_id, current_user.id, data.notes)


@router.post("/{complaint_id}/feedback")
async def post_feedback(
    complaint_id: str,
    data: FeedbackCreate,
    current_user: UserInDB = Depends(require_roles(Role.CITIZEN)),
):
    return await submit_feedback(
        complaint_id, current_user.id, data.rating, data.comment
    )
