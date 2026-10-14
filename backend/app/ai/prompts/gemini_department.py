"""Prompt template for Gemini department routing (6 departments)."""

from app.ai.departments_config import (
    COMPLAINT_CATEGORIES,
    PRIORITY_LEVELS,
    ROUTING_DEPARTMENT_CODES,
    UNSUPPORTED_DEPARTMENT_CODE,
    format_routing_department_list,
)


def build_gemini_department_prompt(
    *,
    title: str,
    description: str,
    departments: list[dict],
    address: str | None = None,
) -> str:
    dept_lines = []
    for d in departments:
        code = d.get("code", "")
        if code not in ROUTING_DEPARTMENT_CODES:
            continue
        keywords = ", ".join(d.get("keywords") or [])
        dept_lines.append(
            f"- {code}: {d['name']} — {d.get('description', '')}. Examples: {keywords}"
        )

    categories = ", ".join(COMPLAINT_CATEGORIES)
    location_line = f"\nLocation: {address}" if address else ""

    available = format_routing_department_list(departments)
    active_codes = [
        str(d.get("code", "")).upper()
        for d in departments
        if d.get("code") in ROUTING_DEPARTMENT_CODES
    ]
    allowed_codes = ", ".join(active_codes) if active_codes else ", ".join(ROUTING_DEPARTMENT_CODES)

    return f"""You are Humanizr, a municipal civic complaint router. This city portal handles ONLY these departments:
{available}

Task: Read the citizen's title, description, and any attached photos. Route to exactly ONE of our department codes, OR mark the issue as outside our portal.

Rules:
- Valid department codes: {allowed_codes}, OR {UNSUPPORTED_DEPARTMENT_CODE} when the issue is NOT handled by any department above.
- Use {UNSUPPORTED_DEPARTMENT_CODE} when the complaint clearly needs police, fire, health/hospital, education, property tax, telecom/private utility, or any service outside the six departments — do NOT force-fit into the closest department.
- If ambiguous but plausibly related to one of our six departments, pick the best match and lower confidence.
- Use ONLY these categories: {categories}.
- Use ONLY these priority levels: {", ".join(PRIORITY_LEVELS)} (critical = safety/emergency; high = urgent public harm; medium = normal; low = minor).
- Do not invent department codes.

Departments (scope):
{chr(10).join(dept_lines)}

When department_code is {UNSUPPORTED_DEPARTMENT_CODE}, include suggested_external_department (plain English name of who should handle it, e.g. "Police", "Fire department").

Respond with JSON only (no markdown):
{{"department_code":"SAN","category":"garbage","priority":"high","confidence":0.85,"summary":"one sentence for officials","reason":"brief routing rationale","priority_reason":"why this priority","suggested_external_department":null}}

Example out of scope:
{{"department_code":"{UNSUPPORTED_DEPARTMENT_CODE}","category":"other","priority":"medium","confidence":0.9,"summary":"Citizen reported a crime; not handled by this portal.","reason":"Requires law enforcement, not municipal works/sanitation/water/electricity/traffic/parks.","priority_reason":"medium","suggested_external_department":"Police"}}

Complaint title: {title}
Complaint description: {description}{location_line}
"""
