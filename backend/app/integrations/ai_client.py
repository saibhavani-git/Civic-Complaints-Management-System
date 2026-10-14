"""Optional external AI microservice client."""

import logging

import httpx

from app.ai.pipeline import process_complaint_ai
from app.config import get_settings

logger = logging.getLogger(__name__)


async def run_ai_pipeline(
    *,
    title: str,
    description: str,
    location: dict,
    complaint_id: str,
    image_urls: list[str] | None = None,
    image_count: int = 0,
) -> dict:
    settings = get_settings()
    if not settings.AI_SERVICE_URL:
        return await process_complaint_ai(
            title=title,
            description=description,
            location=location,
            complaint_id=complaint_id,
            image_urls=image_urls,
            image_count=image_count,
        )

    url = settings.AI_SERVICE_URL.rstrip("/") + "/api/v1/pipeline"
    payload = {
        "title": title,
        "description": description,
        "latitude": location["lat"],
        "longitude": location["lng"],
        "complaint_id": complaint_id,
        "image_count": image_count,
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.warning("AI service unavailable, falling back to embedded pipeline: %s", exc)
        return await process_complaint_ai(
            title=title,
            description=description,
            location=location,
            complaint_id=complaint_id,
            image_urls=image_urls,
            image_count=image_count,
        )
