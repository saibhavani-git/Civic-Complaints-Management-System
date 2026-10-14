"""Download complaint images for multimodal AI."""

import io
import logging
from typing import Optional

import httpx
from PIL import Image

logger = logging.getLogger(__name__)


async def fetch_image(url: str) -> Optional[Image.Image]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content)).convert("RGB")
    except Exception as exc:
        logger.warning("Could not fetch image %s: %s", url[:80], exc)
        return None
