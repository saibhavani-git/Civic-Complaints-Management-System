"""Copy citizen full_name/email/phone onto complaints missing reporter_* fields."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings


async def main() -> None:
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]

    updated = 0
    async for doc in db.complaints.find({"citizen_id": {"$exists": True}}):
        if doc.get("reporter_email") and doc.get("reporter_full_name"):
            continue
        cid = doc.get("citizen_id")
        if not isinstance(cid, ObjectId):
            try:
                cid = ObjectId(str(cid))
            except Exception:
                continue
        user = await db.users.find_one({"_id": cid}, {"full_name": 1, "email": 1, "phone": 1})
        if not user:
            continue
        await db.complaints.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "reporter_full_name": user.get("full_name"),
                    "reporter_email": user.get("email"),
                    "reporter_phone": user.get("phone"),
                }
            },
        )
        updated += 1

    print(f"Backfilled reporter snapshot on {updated} complaint(s).")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
