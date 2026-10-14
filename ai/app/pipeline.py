from datetime import datetime, timezone

from app.category import classify_category
from app.priority import predict_priority


async def run_pipeline(
    *,
    title: str,
    description: str,
    location: dict,
    complaint_id: str,
    image_count: int,
) -> dict:
    text = f"{title}. {description}"
    category = classify_category(text)
    priority = predict_priority(text)
    image_verified = image_count > 0

    return {
        "summary": text[:180],
        "category": category["category"],
        "category_confidence": category["confidence"],
        "predicted_priority": priority,
        "confidence_score": category["confidence"],
        "is_duplicate": False,
        "image_verification": {
            "verified": image_verified,
            "confidence": 0.7 if image_verified else 0.0,
            "image_count": image_count,
        },
        "classification": category,
        "priority_prediction": {"level": priority, "confidence": 0.75},
        "duplicate_check": {"is_duplicate": False},
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "processing_time_ms": 5,
        "complaint_id": complaint_id,
        "location": location,
    }
