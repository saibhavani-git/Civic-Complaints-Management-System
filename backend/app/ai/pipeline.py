"""Production AI pipeline: Gemini routing + priority → duplicates → dept admin queue."""

import logging
from datetime import datetime, timezone

from bson import ObjectId

from app.ai.category_classifier import classify_category
from app.ai.duplicate_detector import detect_duplicate
from app.ai.gemini_router import classify_complaint_with_gemini
from app.ai.image_verifier import verify_images
from app.db.database import get_database

logger = logging.getLogger(__name__)


async def _persist_ai_result(complaint_id: str, result: dict) -> str:
    db = get_database()
    doc = {
        "complaint_id": ObjectId(complaint_id),
        "classification": result.get("classification"),
        "priority": result.get("priority_prediction"),
        "duplicate_check": result.get("duplicate_check"),
        "image_verification": result.get("image_verification"),
        "routing": result.get("routing"),
        "embedding": result.get("embedding"),
        "model_versions": result.get("model_versions"),
        "processing_time_ms": result.get("processing_time_ms"),
        "created_at": datetime.now(timezone.utc),
    }
    await db.ai_results.replace_one(
        {"complaint_id": ObjectId(complaint_id)},
        doc,
        upsert=True,
    )
    return complaint_id


async def _link_duplicate_group(complaint_id: str, primary_id: str, similarity: float) -> None:
    db = get_database()
    primary_oid = ObjectId(primary_id)
    complaint_oid = ObjectId(complaint_id)

    group = await db.duplicate_groups.find_one({"primary_complaint_id": primary_oid, "status": "active"})
    if group:
        await db.duplicate_groups.update_one(
            {"_id": group["_id"]},
            {"$addToSet": {"complaint_ids": complaint_oid}, "$set": {"updated_at": datetime.now(timezone.utc)}},
        )
    else:
        await db.duplicate_groups.insert_one(
            {
                "primary_complaint_id": primary_oid,
                "complaint_ids": [primary_oid, complaint_oid],
                "similarity_score": similarity,
                "status": "active",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        )

    await db.complaints.update_one(
        {"_id": complaint_oid},
        {"$set": {"duplicate_of_id": primary_oid, "is_primary_in_group": False}},
    )


def _priority_from_gemini(gemini: dict | None) -> tuple[str, dict]:
    if gemini and gemini.get("priority"):
        level = gemini["priority"]
        return level, {
            "level": level,
            "confidence": gemini.get("confidence", 0.75),
            "source": "gemini",
            "reason": gemini.get("priority_reason") or gemini.get("reason"),
            "factors": [],
        }
    return "medium", {
        "level": "medium",
        "confidence": 0.0,
        "source": "default",
        "reason": "Gemini unavailable — default priority applied",
        "factors": [],
    }


async def process_complaint_ai(
    title: str,
    description: str,
    location: dict,
    complaint_id: str,
    image_urls: list[str] | None = None,
    image_count: int = 0,
) -> dict:
    import time

    started = time.perf_counter()
    text = f"{title}. {description}"
    urls = image_urls or []
    address = location.get("address") if isinstance(location, dict) else None

    gemini = await classify_complaint_with_gemini(
        title,
        description,
        urls,
        address=address,
    )

    category_result = classify_category(text)
    unsupported = bool(gemini and gemini.get("unsupported"))
    category = (gemini or {}).get("category") or category_result["category"]
    summary = (gemini or {}).get("summary") or text[:200]
    department_id = None if unsupported else (gemini or {}).get("department_id")

    priority_level, priority_result = _priority_from_gemini(gemini)

    if unsupported:
        routing = {
            "unsupported": True,
            "department_id": None,
            "department_name": None,
            "department_code": gemini.get("department_code"),
            "suggested_external_department": gemini.get("suggested_external_department"),
            "public_message": gemini.get("public_message"),
            "confidence": gemini.get("confidence", 0.0),
            "routing_source": "unsupported",
            "reason": gemini.get("reason"),
        }
    else:
        routing = {
            "unsupported": False,
            "department_id": department_id,
            "department_name": (gemini or {}).get("department_name"),
            "department_code": (gemini or {}).get("department_code"),
            "confidence": (gemini or {}).get("confidence", 0.0),
            "routing_source": "gemini" if gemini else "unclassified",
            "reason": (gemini or {}).get("reason"),
        }

    duplicate_result = await detect_duplicate(text, complaint_id, location)

    image_result = verify_images(
        category,
        len(urls) or image_count,
        title,
        description,
        image_routing=None,
    )

    duplicate_of = duplicate_result.get("duplicate_of")
    if duplicate_result["is_duplicate"] and duplicate_of:
        await _link_duplicate_group(
            complaint_id,
            duplicate_of,
            duplicate_result.get("similarity_score") or 0.0,
        )

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    model_versions = {"production": "gemini-routing-and-priority-v1"}

    ai_payload = {
        "summary": summary,
        "category": category,
        "category_confidence": category_result["confidence"],
        "predicted_department": routing.get("department_name"),
        "predicted_priority": priority_level,
        "confidence_score": routing.get("confidence", 0.0),
        "unsupported_department": unsupported,
        "public_message": routing.get("public_message") if unsupported else None,
        "is_duplicate": duplicate_result["is_duplicate"],
        "duplicate_of": duplicate_of,
        "similarity_score": duplicate_result.get("similarity_score"),
        "similar_nearby_count": duplicate_result.get("similar_nearby_count", 0),
        "embedding": duplicate_result.get("embedding"),
        "image_verification": image_result,
        "routing": routing,
        "department_id": department_id,
        "assigned_officer_id": None,
        "processed_at": datetime.now(timezone.utc),
        "classification": category_result,
        "priority_prediction": priority_result,
        "duplicate_check": duplicate_result,
        "processing_time_ms": elapsed_ms,
        "model_versions": model_versions,
    }

    await _persist_ai_result(complaint_id, ai_payload)
    return ai_payload
