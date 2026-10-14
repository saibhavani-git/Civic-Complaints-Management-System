from fastapi import APIRouter, Depends

from app.core.rbac import Role, require_roles
from app.services.blockchain_service import get_complaint_chain, verify_complaint_chain

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/complaints/{complaint_id}/chain")
async def complaint_audit_chain(
    complaint_id: str,
    _=Depends(require_roles(Role.OFFICER, Role.DEPT_ADMIN, Role.ADMIN)),
):
    return {"items": await get_complaint_chain(complaint_id)}


@router.get("/complaints/{complaint_id}/verify")
async def verify_chain(
    complaint_id: str,
    _=Depends(require_roles(Role.ADMIN)),
):
    return await verify_complaint_chain(complaint_id)
