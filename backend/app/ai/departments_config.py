"""Six municipal departments used for live Gemini routing."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

# Must match `seed_departments` in app/db/init_db.py
ROUTING_DEPARTMENT_CODES: tuple[str, ...] = ("PWD", "SAN", "WSD", "ELEC", "TNT", "PAR")

# Gemini must return this code when the issue is outside our configured departments.
UNSUPPORTED_DEPARTMENT_CODE = "UNSUPPORTED"

_UNSUPPORTED_ROUTING_CODES: frozenset[str] = frozenset(
    {UNSUPPORTED_DEPARTMENT_CODE, "NONE", "NA", "N/A", "OTHER", "OUT_OF_SCOPE"}
)

PRIORITY_LEVELS: tuple[str, ...] = ("low", "medium", "high", "critical")

COMPLAINT_CATEGORIES: tuple[str, ...] = (
    "road_damage",
    "garbage",
    "water",
    "electricity",
    "traffic",
    "parks",
    "other",
)


def format_routing_department_list(
    departments: list[dict[str, Any]],
    *,
    include_codes: bool = True,
) -> str:
    parts = []
    for d in departments:
        code = d.get("code", "")
        if code not in ROUTING_DEPARTMENT_CODES:
            continue
        name = d.get("name", code)
        parts.append(f"{name} ({code})" if include_codes else str(name))
    if parts:
        return ", ".join(parts)
    if include_codes:
        return ", ".join(ROUTING_DEPARTMENT_CODES)
    return "roads, sanitation, water, electricity, traffic, and parks"


def is_unsupported_department_code(code: str | None) -> bool:
    if not code:
        return False
    return str(code).upper().strip() in _UNSUPPORTED_ROUTING_CODES


async def load_routing_departments(db: AsyncIOMotorDatabase) -> list[dict[str, Any]]:
    """Active departments limited to the six Humanizr routing codes."""
    cursor = db.departments.find(
        {"is_active": True, "code": {"$in": list(ROUTING_DEPARTMENT_CODES)}},
        {"name": 1, "code": 1, "description": 1, "keywords": 1},
    )
    docs = [doc async for doc in cursor]
    order = {code: i for i, code in enumerate(ROUTING_DEPARTMENT_CODES)}
    docs.sort(key=lambda d: order.get(d.get("code", ""), 99))
    return docs
