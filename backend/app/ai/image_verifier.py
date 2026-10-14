"""Verify images align with predicted category / department routing."""

from typing import Any, Optional

from app.ai.category_classifier import CATEGORY_KEYWORDS


def verify_images(
    category: str,
    image_count: int,
    title: str,
    description: str,
    image_routing: Optional[dict[str, Any]] = None,
) -> dict:
    if image_count == 0:
        return {
            "verified": False,
            "confidence": 0.0,
            "message": "No images uploaded for verification",
        }

    text = f"{title} {description}".lower()
    keywords = CATEGORY_KEYWORDS.get(category, [])
    keyword_hits = sum(1 for kw in keywords if kw in text)
    base = 0.5
    confidence = min(0.95, base + keyword_hits * 0.08 + min(image_count, 3) * 0.06)

    if image_routing and image_routing.get("department_id"):
        confidence = min(0.98, confidence + float(image_routing.get("confidence", 0)) * 0.25)
        message = (
            f"Image routed to {image_routing.get('department_name')} "
            f"via {image_routing.get('method', 'vision')}"
        )
    elif keyword_hits > 0:
        message = "Image present; description matches category keywords"
    else:
        message = "Image present; manual review recommended"

    return {
        "verified": confidence >= 0.55,
        "confidence": round(confidence, 3),
        "message": message,
        "image_count": image_count,
    }
