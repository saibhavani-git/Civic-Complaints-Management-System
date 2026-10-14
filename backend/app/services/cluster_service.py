"""Area cluster detection — recommend systemic fixes over one-off tickets."""

import logging
from datetime import datetime, timezone

from bson import ObjectId

from app.config import get_settings
from app.db.database import get_database

logger = logging.getLogger(__name__)

CATEGORY_LABELS = {
    "road": "road surface",
    "garbage": "sanitation",
    "drainage": "drainage",
    "water": "water supply",
    "street_light": "street lighting",
    "traffic": "traffic",
    "parks": "parks and trees",
    "other": "civic infrastructure",
}


def _suggested_action(category: str, count: int, address_hint: str) -> str:
    label = CATEGORY_LABELS.get(category, "infrastructure")
    area = address_hint.split(",")[0].strip() if address_hint else "this area"
    return (
        f"Cluster detected: {count} {label} complaints near {area}. "
        f"Recommend a coordinated {label} remediation project instead of isolated fixes."
    )


async def refresh_clusters_for_location(
    latitude: float,
    longitude: float,
    category: str,
    exclude_complaint_id: str | None = None,
) -> dict | None:
    settings = get_settings()
    db = get_database()
    radius_m = settings.CLUSTER_RADIUS_METERS
    min_count = settings.CLUSTER_MIN_COMPLAINTS

    query: dict = {
        "category": category,
        "status": {"$nin": ["rejected", "closed"]},
        "$or": [{"duplicate_of_id": {"$exists": False}}, {"duplicate_of_id": None}],
        "location": {
            "$nearSphere": {
                "$geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                "$maxDistance": radius_m,
            }
        },
    }
    if exclude_complaint_id:
        query["_id"] = {"$ne": ObjectId(exclude_complaint_id)}

    nearby = await db.complaints.find(query).limit(200).to_list(length=200)
    if len(nearby) < min_count:
        return None

    complaint_ids = [doc["_id"] for doc in nearby]
    address_hint = nearby[0].get("location", {}).get("address", "nearby locality")
    action = _suggested_action(category, len(nearby), address_hint)

    existing = await db.clusters.find_one(
        {
            "category": category,
            "status": {"$in": ["detected", "acknowledged", "in_progress"]},
            "centroid": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                    "$maxDistance": radius_m,
                }
            },
        }
    )

    now = datetime.now(timezone.utc)
    if existing:
        merged_ids = list({*(existing.get("complaint_ids") or []), *complaint_ids})
        await db.clusters.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "complaint_ids": merged_ids,
                    "complaint_count": len(merged_ids),
                    "suggested_action": action,
                    "updated_at": now,
                }
            },
        )
        cluster_id = existing["_id"]
    else:
        result = await db.clusters.insert_one(
            {
                "name": f"{category.replace('_', ' ').title()} cluster",
                "category": category,
                "centroid": {"type": "Point", "coordinates": [longitude, latitude]},
                "radius_meters": radius_m,
                "complaint_ids": complaint_ids,
                "complaint_count": len(complaint_ids),
                "suggested_action": action,
                "priority": "high" if len(nearby) >= min_count * 2 else "medium",
                "status": "detected",
                "detected_at": now,
                "updated_at": now,
            }
        )
        cluster_id = result.inserted_id

    await db.complaints.update_many(
        {"_id": {"$in": complaint_ids}},
        {"$set": {"cluster_id": cluster_id}},
    )
    logger.info("Cluster %s updated with %s complaints", cluster_id, len(complaint_ids))
    return {"cluster_id": str(cluster_id), "complaint_count": len(complaint_ids), "suggested_action": action}


async def list_clusters(department_id: str | None = None, limit: int = 50) -> list[dict]:
    db = get_database()
    query: dict = {"status": {"$ne": "resolved"}}
    if department_id:
        query["department_id"] = ObjectId(department_id)

    cursor = db.clusters.find(query).sort("complaint_count", -1).limit(limit)
    items = []
    async for doc in cursor:
        items.append(
            {
                "id": str(doc["_id"]),
                "name": doc["name"],
                "category": doc["category"],
                "complaint_count": doc.get("complaint_count", 0),
                "suggested_action": doc.get("suggested_action"),
                "priority": doc.get("priority", "medium"),
                "status": doc.get("status", "detected"),
                "centroid": doc.get("centroid"),
                "detected_at": doc.get("detected_at"),
            }
        )
    return items
