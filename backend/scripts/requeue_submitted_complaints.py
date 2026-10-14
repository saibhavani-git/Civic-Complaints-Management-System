"""Re-enqueue complaints stuck in `submitted` (e.g. after fixing BACKEND_URL on queue worker)."""

import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.db.database import connect_db, get_database
from app.integrations.queue_client import enqueue_complaint_ai


async def main() -> None:
    await connect_db()
    db = get_database()
    cursor = db.complaints.find({"status": "submitted"}).sort("created_at", 1)
    n = 0
    ok = 0
    async for doc in cursor:
        oid = str(doc["_id"])
        ref = doc.get("complaint_id")
        if await enqueue_complaint_ai(oid):
            print(f"Enqueued {ref} ({oid})")
            ok += 1
        else:
            print(f"FAILED enqueue {ref} ({oid}) — is queue running on 3030?")
        n += 1
    print(f"Done — {ok}/{n} complaint(s) accepted by queue service.")


if __name__ == "__main__":
    asyncio.run(main())
