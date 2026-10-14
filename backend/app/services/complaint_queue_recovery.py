"""Re-enqueue complaints stuck in submitted / ai_processing (queue or worker outages)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from bson import ObjectId

from app.db.database import get_database
from app.integrations.queue_client import enqueue_complaint_ai, queue_service_reachable
from app.schemas.complaint import ComplaintStatus

logger = logging.getLogger(__name__)

# Submitted longer than this with no progress → try enqueue again.
STALE_SUBMITTED_AFTER = timedelta(minutes=3)
# ai_processing with no update → worker/API likely died mid-flight.
STALE_AI_PROCESSING_AFTER = timedelta(minutes=12)


async def _recover_one(oid: str, ref: str | None, *, allow_direct: bool) -> bool:
    if await enqueue_complaint_ai(oid):
        logger.info("Recovery enqueued complaint %s", ref or oid)
        return True
    if not allow_direct:
        return False
    if not await queue_service_reachable():
        logger.warning("Queue down — running in-process AI for %s", ref or oid)
        from app.services.complaint_service import process_queued_complaint_ai

        await process_queued_complaint_ai(oid)
        return True
    return False


async def recover_stale_complaints(*, limit: int = 50) -> int:
    """Return count of complaints re-enqueued or processed."""
    db = get_database()
    now = datetime.now(timezone.utc)
    seen: set[str] = set()
    count = 0

    submitted_cutoff = now - STALE_SUBMITTED_AFTER
    async for doc in db.complaints.find(
        {
            "status": ComplaintStatus.SUBMITTED.value,
            "updated_at": {"$lt": submitted_cutoff},
        }
    ).sort("updated_at", 1).limit(limit):
        oid = str(doc["_id"])
        if oid in seen:
            continue
        seen.add(oid)
        if await _recover_one(oid, doc.get("complaint_id"), allow_direct=True):
            count += 1

    ai_cutoff = now - STALE_AI_PROCESSING_AFTER
    async for doc in db.complaints.find(
        {
            "status": ComplaintStatus.AI_PROCESSING.value,
            "updated_at": {"$lt": ai_cutoff},
        }
    ).sort("updated_at", 1).limit(limit):
        oid = str(doc["_id"])
        if oid in seen:
            continue
        seen.add(oid)
        if await _recover_one(oid, doc.get("complaint_id"), allow_direct=True):
            count += 1

    return count


async def list_pipeline_stuck(*, limit: int = 20) -> list[dict]:
    """Debug: complaints still in early pipeline."""
    db = get_database()
    now = datetime.now(timezone.utc)
    out: list[dict] = []
    query = {
        "status": {
            "$in": [ComplaintStatus.SUBMITTED.value, ComplaintStatus.AI_PROCESSING.value],
        }
    }
    async for doc in db.complaints.find(query).sort("updated_at", 1).limit(limit):
        updated = doc.get("updated_at")
        age_min = None
        if isinstance(updated, datetime):
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            age_min = round((now - updated).total_seconds() / 60, 1)
        out.append(
            {
                "complaint_id": doc.get("complaint_id"),
                "id": str(doc["_id"]),
                "status": doc.get("status"),
                "updated_at": updated.isoformat() if isinstance(updated, datetime) else None,
                "age_minutes": age_min,
            }
        )
    return out
