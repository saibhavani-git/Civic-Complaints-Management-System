"""Print recent complaints for demo / QA."""
import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings


async def main() -> None:
    s = get_settings()
    client = AsyncIOMotorClient(s.MONGODB_URI)
    db = client[s.MONGODB_DB_NAME]
    print("--- Recent complaints (newest 10) ---\n")
    async for doc in db.complaints.find({}).sort("updated_at", -1).limit(10):
        citizen = (
            await db.users.find_one({"_id": doc["citizen_id"]}, {"email": 1, "full_name": 1})
            if doc.get("citizen_id")
            else None
        )
        dept = (
            await db.departments.find_one({"_id": doc["department_id"]}, {"code": 1, "name": 1})
            if doc.get("department_id")
            else None
        )
        title = (doc.get("title") or "")[:55]
        print(f"{doc.get('complaint_id')}  [{doc.get('status')}]")
        print(f"  {title}")
        if citizen:
            print(f"  Reporter: {citizen.get('full_name')} ({citizen.get('email')})")
        if dept:
            print(f"  Dept: {dept.get('code')} — {dept.get('name')}")
        print(f"  Open in app: http://localhost:3000 (login as reporter or staff)\n")
    print("Total complaints:", await db.complaints.count_documents({}))
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
