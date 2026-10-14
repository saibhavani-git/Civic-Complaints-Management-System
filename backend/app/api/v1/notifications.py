from fastapi import APIRouter, Depends

from app.core.rbac import get_current_user
from app.schemas.user import UserInDB
from app.services.notification_service import (
    get_user_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def list_notifications(
    unread_only: bool = False,
    current_user: UserInDB = Depends(get_current_user),
):
    return await get_user_notifications(current_user.id, unread_only)


@router.patch("/read-all", status_code=204)
async def mark_all_read(current_user: UserInDB = Depends(get_current_user)):
    await mark_all_notifications_read(current_user.id)


@router.patch("/{notification_id}/read", status_code=204)
async def mark_read(
    notification_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    await mark_notification_read(notification_id, current_user.id)
