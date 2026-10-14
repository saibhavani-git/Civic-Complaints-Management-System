from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase


async def create_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.users.create_index("email", unique=True)
    await db.users.create_index("role")
    await db.users.create_index("department_id")

    await db.departments.create_index("code", unique=True)

    await db.complaints.create_index("complaint_id", unique=True)
    await db.complaints.create_index([("citizen_id", 1), ("created_at", -1)])
    await db.complaints.create_index([("assigned_officer_id", 1), ("status", 1)])
    await db.complaints.create_index([("department_id", 1), ("status", 1)])
    await db.complaints.create_index([("status", 1), ("created_at", 1)])
    await db.complaints.create_index("priority")
    await db.complaints.create_index([("location", "2dsphere")])
    await db.complaints.create_index("created_at")

    await db.notifications.create_index([("user_id", 1), ("is_read", 1), ("created_at", -1)])
    await db.refresh_tokens.create_index("expires_at", expireAfterSeconds=0)
    await db.feedback.create_index("complaint_id", unique=True)

    await db.ai_results.create_index("complaint_id", unique=True)
    await db.duplicate_groups.create_index("primary_complaint_id")
    await db.clusters.create_index([("centroid", "2dsphere")])
    await db.clusters.create_index("category")
    await db.blockchain_ledger.create_index([("complaint_id", 1), ("block_index", 1)])


async def seed_departments(db: AsyncIOMotorDatabase) -> None:
    if await db.departments.count_documents({}) > 0:
        return

    departments = [
        {
            "name": "Public Works Department",
            "code": "PWD",
            "description": "Roads, streetlights, infrastructure",
            "keywords": ["road", "pothole", "streetlight", "bridge", "footpath", "drainage"],
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "name": "Sanitation Department",
            "code": "SAN",
            "description": "Garbage collection, cleanliness",
            "keywords": ["garbage", "waste", "sanitation", "cleanliness", "dump", "sewage"],
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "name": "Water Supply Department",
            "code": "WSD",
            "description": "Water supply and pipeline issues",
            "keywords": ["water", "pipeline", "leak", "supply", "tap", "contamination"],
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "name": "Electricity Department",
            "code": "ELEC",
            "description": "Power supply and electrical infrastructure",
            "keywords": ["electricity", "power", "transformer", "outage", "wire", "meter"],
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "name": "Traffic & Transport",
            "code": "TNT",
            "description": "Traffic signals, public transport",
            "keywords": ["traffic", "signal", "bus", "parking", "accident", "transport"],
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "name": "Parks & Recreation",
            "code": "PAR",
            "description": "Parks, playgrounds, green spaces",
            "keywords": ["park", "playground", "garden", "tree", "green", "recreation"],
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        },
    ]
    await db.departments.insert_many(departments)
