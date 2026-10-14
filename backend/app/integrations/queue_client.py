import asyncio
import logging
from datetime import datetime, timezone

import httpx
from bson import ObjectId

from app.config import get_settings
from app.db.database import get_database

logger = logging.getLogger(__name__)

ENQUEUE_RETRIES = 3
ENQUEUE_TIMEOUT_SEC = 45.0


async def enqueue_complaint_ai(complaint_id: str) -> bool:
    """Add complaint to BullMQ via the Node queue service. Returns True if accepted."""
    settings = get_settings()
    base = (settings.QUEUE_SERVICE_URL or "").strip().rstrip("/")
    if not base:
        logger.error("QUEUE_SERVICE_URL not set — complaint %s not enqueued", complaint_id)
        await _mark_enqueue_failed(complaint_id, "QUEUE_SERVICE_URL not set")
        return False

    url = f"{base}/enqueue/complaint-ai"
    last_exc: Exception | None = None
    for attempt in range(ENQUEUE_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=ENQUEUE_TIMEOUT_SEC) as client:
                resp = await client.post(url, json={"complaint_id": complaint_id})
                resp.raise_for_status()
            await _clear_enqueue_failed(complaint_id)
            return True
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Enqueue attempt %s/%s failed for %s: %s",
                attempt + 1,
                ENQUEUE_RETRIES,
                complaint_id,
                exc,
            )
            if attempt + 1 < ENQUEUE_RETRIES:
                await asyncio.sleep(2**attempt)

    logger.error("Failed to enqueue complaint %s after retries: %s", complaint_id, last_exc)
    await _mark_enqueue_failed(complaint_id, str(last_exc) if last_exc else "unknown")
    return False


async def _mark_enqueue_failed(complaint_id: str, reason: str) -> None:
    try:
        db = get_database()
        await db.complaints.update_one(
            {"_id": ObjectId(complaint_id)},
            {
                "$set": {
                    "ai_enqueue_failed_at": datetime.now(timezone.utc),
                    "ai_enqueue_last_error": reason[:500],
                }
            },
        )
    except Exception as exc:
        logger.debug("Could not mark enqueue failure on %s: %s", complaint_id, exc)


async def _clear_enqueue_failed(complaint_id: str) -> None:
    try:
        db = get_database()
        await db.complaints.update_one(
            {"_id": ObjectId(complaint_id)},
            {"$unset": {"ai_enqueue_failed_at": "", "ai_enqueue_last_error": ""}},
        )
    except Exception:
        pass


async def queue_service_reachable() -> bool:
    settings = get_settings()
    base = (settings.QUEUE_SERVICE_URL or "").strip().rstrip("/")
    if not base:
        return False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{base}/health")
            return r.status_code == 200
    except Exception:
        return False
