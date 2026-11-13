from datetime import datetime, timezone

from bson import ObjectId

from app.ai.departments_config import normalize_priority
from app.db.database import get_database
from app.schemas.common import AnalyticsOverview

# Open complaints (not resolved, closed, rejected, or post-resolution feedback).
IN_PROGRESS_STATUSES = [
    "pending",
    "submitted",
    "ai_processing",
    "routed_to_department",
    "ai_processed",
    "verified",
    "assigned",
    "work_started",
    "in_progress",
]


def _dept_match(department_id: ObjectId | None) -> dict:
    if department_id:
        return {"department_id": department_id}
    return {}


async def get_analytics_overview(department_id: ObjectId | None = None) -> AnalyticsOverview:
    db = get_database()
    base = _dept_match(department_id)

    total = await db.complaints.count_documents(base)
    in_progress = await db.complaints.count_documents(
        {**base, "status": {"$in": IN_PROGRESS_STATUSES}}
    )
    resolved = await db.complaints.count_documents({**base, "status": {"$in": ["resolved", "closed"]}})

    priority_pipeline = [
        *([{"$match": base}] if base else []),
        {"$group": {"_id": "$priority", "count": {"$sum": 1}}},
    ]
    priority_dist: dict[str, int] = {"low": 0, "medium": 0, "high": 0}
    async for doc in db.complaints.aggregate(priority_pipeline):
        if doc["_id"]:
            level = normalize_priority(doc["_id"])
            priority_dist[level] = priority_dist.get(level, 0) + doc["count"]

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


_SOLVED_STATUSES = {"resolved", "closed", "feedback_received"}
_REJECTED_STATUSES = {"rejected"}
_AWAITING_CLOSE = {"work_completed"}
_IN_PROGRESS = {"work_started", "in_progress"}
_ASSIGNED_ONLY = {"assigned"}
_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
_CASE_LIST_LIMIT = 40


def _id_variants(value: object) -> list:
    """Match ids stored as ObjectId or string."""
    if isinstance(value, ObjectId):
        return [value, str(value)]
    text = str(value).strip()
    variants: list = [text]
    if ObjectId.is_valid(text):
        variants.append(ObjectId(text))
    return variants


def _case_priority(value: object) -> str:
    return normalize_priority(value)


def _case_status(value: object) -> str:
    text = str(value or "").strip().lower()
    return text or "pending"


def _iso(value: object) -> str | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return None


def _brief_case(
    doc: dict,
    *,
    dept_names: dict[str, dict],
    officer_names: dict[str, str],
) -> dict:
    dept_id = str(doc["department_id"]) if doc.get("department_id") else None
    dept = dept_names.get(dept_id) if dept_id else None
    officer_id = str(doc["assigned_officer_id"]) if doc.get("assigned_officer_id") else None
    location = doc.get("location") or {}
    address = location.get("address") if isinstance(location, dict) else None
    return {
        "id": str(doc["_id"]),
        "complaint_id": doc.get("complaint_id") or "",
        "title": doc.get("title") or "Untitled",
        "status": _case_status(doc.get("status")),
        "priority": _case_priority(doc.get("priority")),
        "category": doc.get("category"),
        "address": address,
        "department_id": dept_id,
        "department_name": dept["name"] if dept else None,
        "department_code": dept["code"] if dept else None,
        "citizen_name": doc.get("reporter_full_name"),
        "officer_name": officer_names.get(officer_id) if officer_id else None,
        "created_at": _iso(doc.get("created_at")),
        "updated_at": _iso(doc.get("updated_at")),
    }


async def get_person_case_report(user_id: str) -> dict | None:
    """Solved, open, and critical cases for one admin, officer, department head, or resident."""
    db = get_database()
    if not ObjectId.is_valid(user_id):
        return None
    oid = ObjectId(user_id)
    user = await db.users.find_one({"_id": oid}, {"password_hash": 0})
    if not user:
        return None

    role = str(user.get("role") or "citizen")
    scope = "none"
    query: dict | None = None
    if role == "officer":
        scope = "assigned"
        query = {"assigned_officer_id": {"$in": _id_variants(oid)}}
    elif role == "citizen":
        scope = "reported"
        query = {"citizen_id": {"$in": _id_variants(oid)}}
    elif role == "dept_admin" and user.get("department_id"):
        scope = "department"
        query = {"department_id": {"$in": _id_variants(user["department_id"])}}

    dept_by_id: dict[str, dict] = {}
    async for dept in db.departments.find({}, {"name": 1, "code": 1}):
        dept_by_id[str(dept["_id"])] = {"name": dept.get("name"), "code": dept.get("code")}

    user_dept_id = str(user["department_id"]) if user.get("department_id") else None
    user_dept = dept_by_id.get(user_dept_id) if user_dept_id else None

    docs: list[dict] = []
    if query is not None:
        cursor = db.complaints.find(
            query,
            {
                "complaint_id": 1,
                "title": 1,
                "status": 1,
                "priority": 1,
                "category": 1,
                "location.address": 1,
                "department_id": 1,
                "assigned_officer_id": 1,
                "reporter_full_name": 1,
                "created_at": 1,
                "updated_at": 1,
            },
        )
        async for doc in cursor:
            docs.append(doc)

    officer_ids: list[ObjectId] = []
    seen_officers: set[str] = set()
    for doc in docs:
        raw = doc.get("assigned_officer_id")
        if not raw:
            continue
        key = str(raw)
        if key in seen_officers or not ObjectId.is_valid(key):
            continue
        seen_officers.add(key)
        officer_ids.append(ObjectId(key))

    officer_names: dict[str, str] = {}
    if officer_ids:
        async for officer in db.users.find({"_id": {"$in": officer_ids}}, {"full_name": 1}):
            officer_names[str(officer["_id"])] = officer.get("full_name") or ""

    solved_docs: list[dict] = []
    current_docs: list[dict] = []
    critical_docs: list[dict] = []
    rejected = 0
    high = medium = low = 0
    awaiting_close = assigned_count = in_progress = waiting_assignment = 0
    critical_solved = 0

    for doc in docs:
        status = _case_status(doc.get("status"))
        priority = _case_priority(doc.get("priority"))
        if status in _SOLVED_STATUSES:
            solved_docs.append(doc)
            if priority == "critical":
                critical_solved += 1
            continue
        if status in _REJECTED_STATUSES:
            rejected += 1
            continue
        current_docs.append(doc)
        if priority == "critical":
            critical_docs.append(doc)
        elif priority == "high":
            high += 1
        elif priority == "low":
            low += 1
        else:
            medium += 1
        if status in _AWAITING_CLOSE:
            awaiting_close += 1
        elif status in _IN_PROGRESS:
            in_progress += 1
        elif status in _ASSIGNED_ONLY:
            assigned_count += 1
        else:
            waiting_assignment += 1

    def _updated_key(doc: dict) -> datetime:
        value = doc.get("updated_at") or doc.get("created_at")
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return datetime.min.replace(tzinfo=timezone.utc)

    critical_docs.sort(key=_updated_key, reverse=True)
    current_docs.sort(
        key=lambda doc: (_PRIORITY_RANK.get(_case_priority(doc.get("priority")), 9), -_updated_key(doc).timestamp()),
    )
    solved_docs.sort(key=_updated_key, reverse=True)

    def _pack(items: list[dict]) -> list[dict]:
        return [
            _brief_case(doc, dept_names=dept_by_id, officer_names=officer_names)
            for doc in items[:_CASE_LIST_LIMIT]
        ]

    total = len(docs)
    solved = len(solved_docs)
    current = len(current_docs)
    return {
        "person": {
            "id": user_id,
            "full_name": user.get("full_name") or "",
            "email": user.get("email") or "",
            "phone": user.get("phone"),
            "role": role,
            "is_active": user.get("is_active", True),
            "department_id": user_dept_id,
            "department_name": user_dept["name"] if user_dept else None,
            "department_code": user_dept["code"] if user_dept else None,
            "service_area": (user.get("service_area") or "").strip() or None,
            "scope": scope,
        },
        "summary": {
            "total": total,
            "solved": solved,
            "current": current,
            "critical": len(critical_docs),
            "critical_solved": critical_solved,
            "high": high,
            "medium": medium,
            "low": low,
            "rejected": rejected,
            "awaiting_close": awaiting_close,
            "assigned": assigned_count,
            "in_progress": in_progress,
            "waiting_assignment": waiting_assignment,
            "resolution_rate": round((solved / total * 100) if total else 0, 1),
        },
        "list_limit": _CASE_LIST_LIMIT,
        "critical": _pack(critical_docs),
        "current": _pack(current_docs),
        "solved": _pack(solved_docs),
    }


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
