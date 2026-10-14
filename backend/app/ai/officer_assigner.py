"""Assign officer by department with lowest active workload (or primary duplicate's officer)."""

import logging

from bson import ObjectId

from app.db.database import get_database

logger = logging.getLogger(__name__)


async def assign_officer_for_complaint(
    department_id: str,
    *,
    duplicate_of: str | None = None,
) -> str | None:
    db = get_database()

    if duplicate_of:
        primary = await db.complaints.find_one({"_id": ObjectId(duplicate_of)})
        if primary and primary.get("assigned_officer_id"):
            return str(primary["assigned_officer_id"])

    if not department_id:
        return None

    dept_oid = ObjectId(department_id)
    officers = await db.users.find(
        {"role": "officer", "department_id": dept_oid, "is_active": True}
    ).to_list(50)

    if not officers:
        return None

    best_id = None
    best_load = 10**9

    for officer in officers:
        oid = officer["_id"]
        active = await db.complaints.count_documents(
            {
                "assigned_officer_id": oid,
                "status": {"$nin": ["resolved", "closed", "rejected", "feedback_received"]},
            }
        )
        if active < best_load:
            best_load = active
            best_id = str(oid)

    return best_id
