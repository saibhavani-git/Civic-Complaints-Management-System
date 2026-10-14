import asyncio
import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.rbac import get_current_user
from app.integrations.event_bus import _channel
from app.schemas.user import UserInDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/stream")
async def stream_user_events(current_user: UserInDB = Depends(get_current_user)):
    """Server-Sent Events — complaint + notification updates for the logged-in user."""

    async def event_generator():
        from redis.asyncio import Redis

        from app.config import get_settings

        settings = get_settings()
        channel = _channel(current_user.id)
        redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)

        try:
            yield f"event: connected\ndata: {json.dumps({'type': 'connected'})}\n\n"
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=25.0)
                if message and message.get("type") == "message" and message.get("data"):
                    yield f"event: message\ndata: {message['data']}\n\n"
                else:
                    yield ": keepalive\n\n"
                    await asyncio.sleep(0)
        except asyncio.CancelledError:
            pass
        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.aclose()
                await redis.aclose()
            except Exception as exc:
                logger.debug("SSE cleanup: %s", exc)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
