from datetime import datetime, timezone

from bson import ObjectId

from app.db.database import get_database


async def create_notification(
    user_id: str,
    notif_type: str,
    title: str,
    message: str,
    complaint_id: str | None = None,
) -> None:
    db = get_database()
    await db.notifications.insert_one({
        "user_id": ObjectId(user_id),
        "type": notif_type,
        "title": title,
        "message": message,
        "complaint_id": ObjectId(complaint_id) if complaint_id else None,
        "is_read": False,
        "created_at": datetime.now(timezone.utc),
    })
    from app.integrations.event_bus import notify_notifications_updated

    await notify_notifications_updated(user_id)


async def get_user_notifications(user_id: str, unread_only: bool = False) -> list[dict]:
    db = get_database()
    query: dict = {"user_id": ObjectId(user_id)}
    if unread_only:
        query["is_read"] = False

    cursor = db.notifications.find(query).sort("created_at", -1).limit(50)
    results = []
    async for doc in cursor:
        results.append({
            "id": str(doc["_id"]),
            "type": doc["type"],
            "title": doc["title"],
            "message": doc["message"],
            "complaint_id": str(doc["complaint_id"]) if doc.get("complaint_id") else None,
            "is_read": doc["is_read"],
            "created_at": doc["created_at"],
        })
    return results


async def mark_notification_read(notification_id: str, user_id: str) -> None:
    db = get_database()
    doc = await db.notifications.find_one(
        {"_id": ObjectId(notification_id), "user_id": ObjectId(user_id)}
    )
    if not doc:
        return
    query: dict = {"user_id": ObjectId(user_id), "is_read": False, "title": doc["title"]}
    if doc.get("complaint_id"):
        query["complaint_id"] = doc["complaint_id"]
    if doc.get("type"):
        query["type"] = doc["type"]
    await db.notifications.update_many(query, {"$set": {"is_read": True}})


async def mark_all_notifications_read(user_id: str) -> int:
    db = get_database()
    result = await db.notifications.update_many(
        {"user_id": ObjectId(user_id), "is_read": False},
        {"$set": {"is_read": True}},
    )
    return result.modified_count
