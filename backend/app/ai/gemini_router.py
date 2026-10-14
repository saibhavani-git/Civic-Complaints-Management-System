"""Production routing: Gemini multimodal → one of six departments."""

import json
import logging
import re
from typing import Any, Optional

from app.ai.departments_config import (
    COMPLAINT_CATEGORIES,
    PRIORITY_LEVELS,
    UNSUPPORTED_DEPARTMENT_CODE,
    format_routing_department_list,
    is_unsupported_department_code,
    load_routing_departments,
)
from app.ai.media_fetch import fetch_image
from app.ai.prompts.gemini_department import build_gemini_department_prompt
from app.config import get_settings
from app.db.database import get_database

logger = logging.getLogger(__name__)


def _build_unsupported_routing(
    parsed: dict,
    departments: list[dict],
    *,
    fallback_reason: str | None = None,
) -> dict[str, Any]:
    external = (
        parsed.get("suggested_external_department")
        or parsed.get("external_department")
        or parsed.get("suggested_department")
    )
    external = str(external).strip() if external else None
    reason = (parsed.get("reason") or fallback_reason or "Not handled by departments on this portal.").strip()
    available = format_routing_department_list(departments, include_codes=False)
    if external:
        public_message = (
            f"We don't have a department for “{external}” on this portal. "
            f"We only handle: {available}."
        )
    else:
        public_message = (
            f"This complaint doesn't match any department we operate. "
            f"We only handle: {available}."
        )

    category = str(parsed.get("category", "other")).lower().replace(" ", "_")
    if category not in COMPLAINT_CATEGORIES:
        category = "other"

    priority = str(parsed.get("priority", "medium")).lower().strip()
    if priority not in PRIORITY_LEVELS:
        priority = "medium"

    confidence = float(parsed.get("confidence", 0.85))
    confidence = max(0.0, min(1.0, confidence))

    return {
        "unsupported": True,
        "model": f"Gemini ({get_settings().GEMINI_MODEL})",
        "model_id": get_settings().GEMINI_MODEL,
        "modality": "text",
        "department_id": None,
        "department_name": None,
        "department_code": UNSUPPORTED_DEPARTMENT_CODE,
        "suggested_external_department": external,
        "public_message": public_message,
        "category": category,
        "priority": priority,
        "confidence": confidence,
        "summary": parsed.get("summary") or public_message,
        "reason": reason,
        "priority_reason": parsed.get("priority_reason"),
    }


async def classify_complaint_with_gemini(
    title: str,
    description: str,
    image_urls: list[str],
    *,
    address: str | None = None,
) -> Optional[dict[str, Any]]:
    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — cannot route complaint")
        return None

    db = get_database()
    departments = await load_routing_departments(db)
    if not departments:
        logger.error("No routing departments in database — run seed_departments")
        return None

    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)

    prompt = build_gemini_department_prompt(
        title=title,
        description=description,
        departments=departments,
        address=address,
    )

    parts: list = [prompt]
    for url in image_urls[:3]:
        img = await fetch_image(url)
        if img:
            parts.append(img)

    try:
        response = model.generate_content(parts)
        text = (response.text or "").strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        parsed = json.loads(match.group())
        code = str(parsed.get("department_code", "")).upper().strip()
        if parsed.get("unsupported") is True or is_unsupported_department_code(code):
            parsed = {**parsed, "department_code": UNSUPPORTED_DEPARTMENT_CODE}
            result = _build_unsupported_routing(parsed, departments)
            result["modality"] = "text+image" if len(parts) > 1 else "text"
            return result

        dept = next((d for d in departments if d.get("code") == code), None)
        if not dept:
            logger.info("Gemini returned unknown department_code=%s — treating as unsupported", code)
            return _build_unsupported_routing(
                parsed,
                departments,
                fallback_reason=f"Suggested department code “{code}” is not one we operate.",
            )

        category = str(parsed.get("category", "other")).lower().replace(" ", "_")
        if category not in COMPLAINT_CATEGORIES:
            category = "other"

        confidence = float(parsed.get("confidence", 0.75))
        confidence = max(0.0, min(1.0, confidence))

        priority = str(parsed.get("priority", "medium")).lower().strip()
        if priority not in PRIORITY_LEVELS:
            priority = "medium"

        return {
            "unsupported": False,
            "model": f"Gemini ({settings.GEMINI_MODEL})",
            "model_id": settings.GEMINI_MODEL,
            "modality": "text+image" if len(parts) > 1 else "text",
            "department_id": str(dept["_id"]),
            "department_name": dept["name"],
            "department_code": code,
            "category": category,
            "priority": priority,
            "confidence": confidence,
            "summary": parsed.get("summary"),
            "reason": parsed.get("reason"),
            "priority_reason": parsed.get("priority_reason"),
        }
    except Exception as exc:
        logger.warning("Gemini department routing failed: %s", exc)
        return None
