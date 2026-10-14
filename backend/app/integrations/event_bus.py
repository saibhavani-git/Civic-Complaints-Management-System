"""Redis pub/sub — push live updates to SSE clients (no browser polling)."""

import json
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


def _channel(user_id: str) -> str:
    return f"user:{user_id}:events"


async def publish_user_event(user_id: str, payload: dict) -> None:
    if not user_id:
        return
    try:
        from redis.asyncio import Redis

        settings = get_settings()
        redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis.publish(_channel(user_id), json.dumps(payload))
        await redis.aclose()
    except Exception as exc:
        logger.warning("Could not publish realtime event for user %s: %s", user_id, exc)


async def notify_department_admins_complaint_updated(
    *,
    department_id: str,
    complaint_id: str,
    status: str,
) -> None:
    if not department_id:
        return
    try:
        from bson import ObjectId

        from app.db.database import get_database

        db = get_database()
        payload = {
            "type": "complaint_updated",
            "complaint_id": complaint_id,
            "status": status,
        }
        cursor = db.users.find(
            {
                "role": "dept_admin",
                "department_id": ObjectId(department_id),
                "is_active": True,
            },
            {"_id": 1},
        )
        async for admin in cursor:
            await publish_user_event(str(admin["_id"]), payload)
    except Exception as exc:
        logger.warning(
            "Could not notify dept admins for department %s: %s", department_id, exc
        )


async def notify_complaint_updated(
    *,
    complaint_id: str,
    status: str,
    citizen_id: str,
    officer_id: str | None = None,
    department_id: str | None = None,
) -> None:
    payload = {
        "type": "complaint_updated",
        "complaint_id": complaint_id,
        "status": status,
    }
    await publish_user_event(citizen_id, payload)
    if officer_id and officer_id != citizen_id:
        await publish_user_event(officer_id, payload)
    if department_id:
        await notify_department_admins_complaint_updated(
            department_id=department_id,
            complaint_id=complaint_id,
            status=status,
        )


async def notify_notifications_updated(user_id: str) -> None:
    await publish_user_event(user_id, {"type": "notifications_updated"})
