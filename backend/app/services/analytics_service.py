from datetime import datetime, timezone

from bson import ObjectId

from app.db.database import get_database
from app.schemas.common import AnalyticsOverview


def _dept_match(department_id: ObjectId | None) -> dict:
    if department_id:
        return {"department_id": department_id}
    return {}


async def get_analytics_overview(department_id: ObjectId | None = None) -> AnalyticsOverview:
    db = get_database()
    base = _dept_match(department_id)

    total = await db.complaints.count_documents(base)
    pending = await db.complaints.count_documents(
        {
            **base,
            "status": {
                "$in": [
                    "pending",
                    "submitted",
                    "ai_processing",
                    "routed_to_department",
                    "ai_processed",
                    "assigned",
                ]
            },
        }
    )
    in_progress = await db.complaints.count_documents({**base, "status": "in_progress"})
    resolved = await db.complaints.count_documents({**base, "status": {"$in": ["resolved", "closed"]}})

    priority_pipeline = [
        *([{"$match": base}] if base else []),
        {"$group": {"_id": "$priority", "count": {"$sum": 1}}},
    ]
    priority_dist: dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    async for doc in db.complaints.aggregate(priority_pipeline):
        if doc["_id"]:
            priority_dist[doc["_id"]] = doc["count"]

    resolution_pipeline = [
        {
            "$match": {
                **base,
                "status": {"$in": ["resolved", "closed"]},
                "resolution.resolved_at": {"$exists": True},
            }
        },
        {"$project": {
            "hours": {
                "$divide": [
                    {"$subtract": ["$resolution.resolved_at", "$created_at"]},
                    3600000,
                ]
            }
        }},
        {"$group": {"_id": None, "avg_hours": {"$avg": "$hours"}}},
    ]
    avg_hours = 0.0
    async for doc in db.complaints.aggregate(resolution_pipeline):
        avg_hours = round(doc.get("avg_hours", 0), 1)

    resolution_rate = round((resolved / total * 100) if total > 0 else 0, 1)

    return AnalyticsOverview(
        total_complaints=total,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved,
        avg_resolution_hours=avg_hours,
        priority_distribution=priority_dist,
        resolution_rate=resolution_rate,
    )


async def get_complaints_by_department(department_id: ObjectId | None = None) -> list[dict]:
    db = get_database()
    dept_match: dict = {"department_id": {"$exists": True}}
    if department_id:
        dept_match = {"department_id": department_id}
    pipeline = [
        {"$match": dept_match},
        {"$group": {"_id": "$department_id", "count": {"$sum": 1}}},
        {"$lookup": {"from": "departments", "localField": "_id", "foreignField": "_id", "as": "dept"}},
        {"$unwind": "$dept"},
        {"$project": {"department": "$dept.name", "code": "$dept.code", "count": 1}},
        {"$sort": {"count": -1}},
    ]
    results = []
    async for doc in db.complaints.aggregate(pipeline):
        results.append({"department": doc["department"], "code": doc["code"], "count": doc["count"]})
    return results


async def get_complaint_trends(months: int = 12, department_id: ObjectId | None = None) -> list[dict]:
    db = get_database()
    base = _dept_match(department_id)
    pipeline = [
        *([{"$match": base}] if base else []),
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$created_at"}},
            "count": {"$sum": 1},
            "resolved": {"$sum": {"$cond": [{"$in": ["$status", ["resolved", "closed"]]}, 1, 0]}},
        }},
        {"$sort": {"_id": 1}},
        {"$limit": months},
    ]
    results = []
    async for doc in db.complaints.aggregate(pipeline):
        results.append({"month": doc["_id"], "total": doc["count"], "resolved": doc["resolved"]})
    return results


async def get_heatmap_data() -> list[dict]:
    db = get_database()
    cursor = db.complaints.find(
        {"location.coordinates": {"$exists": True}},
        {"location.coordinates": 1, "priority": 1, "title": 1},
    ).limit(1000)

    features = []
    async for doc in cursor:
        coords = doc.get("location", {}).get("coordinates", [])
        if len(coords) == 2:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": coords},
                "properties": {
                    "priority": doc.get("priority", "medium"),
                    "title": doc.get("title", ""),
                },
            })
    return {"type": "FeatureCollection", "features": features}


async def get_officer_workload() -> list[dict]:
    db = get_database()
    pipeline = [
        {"$match": {"assigned_officer_id": {"$exists": True}, "status": {"$nin": ["resolved", "closed", "rejected"]}}},
        {"$group": {"_id": "$assigned_officer_id", "active_count": {"$sum": 1}}},
        {"$lookup": {"from": "users", "localField": "_id", "foreignField": "_id", "as": "officer"}},
        {"$unwind": "$officer"},
        {"$project": {"officer_name": "$officer.full_name", "active_count": 1}},
        {"$sort": {"active_count": -1}},
    ]
    results = []
    async for doc in db.complaints.aggregate(pipeline):
        results.append({"officer_name": doc["officer_name"], "active_count": doc["active_count"]})
    return results
