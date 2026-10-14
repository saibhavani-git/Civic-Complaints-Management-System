"""Pipeline + notifications sanity check (queue, Redis, stuck complaints, clock)."""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import httpx

from app.config import get_settings
from app.db.database import connect_db, close_db, get_database
from app.integrations.queue_client import queue_service_reachable
from app.services.complaint_queue_recovery import list_pipeline_stuck


async def main() -> None:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    print(f"Server UTC now: {now.isoformat()}")
    print(f"Local display (IST): {now.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()

    api = "http://127.0.0.1:8002"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            h = await client.get(f"{api}/health")
            print("API /health:", h.json())
    except Exception as exc:
        print("API /health FAILED:", exc)

    q_ok = await queue_service_reachable()
    print("Queue reachable:", q_ok, settings.QUEUE_SERVICE_URL)

    await connect_db()
    db = get_database()
    stuck = await list_pipeline_stuck(limit=15)
    print(f"\nPipeline (submitted / ai_processing): {len(stuck)} shown")
    for row in stuck:
        print(f"  {row['complaint_id']} status={row['status']} age_min={row['age_minutes']}")

    n_notif = await db.notifications.count_documents({})
    recent = await db.notifications.find({}).sort("created_at", -1).limit(3).to_list(3)
    print(f"\nNotifications in DB: {n_notif} (latest 3 titles)")
    for doc in recent:
        print(f"  - {doc.get('title')} @ {doc.get('created_at')}")

    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
