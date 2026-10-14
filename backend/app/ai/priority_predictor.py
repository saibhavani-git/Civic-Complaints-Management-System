"""Priority from text urgency + duplicate cluster density (high duplicates → higher priority)."""

PRIORITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _text_priority_score(text: str) -> str:
    text_lower = text.lower()

    critical_keywords = [
        "emergency", "danger", "accident", "injury", "fire", "flood",
        "collapse", "electrocution", "gas leak", "explosion", "death",
    ]
    high_keywords = [
        "urgent", "broken", "blocked", "overflow", "contamination",
        "outage", "no water", "no electricity", "fallen tree",
    ]
    medium_keywords = [
        "damaged", "malfunction", "not working", "leak", "crack",
        "missing", "vandalism", "graffiti", "pothole",
    ]

    critical_count = sum(1 for kw in critical_keywords if kw in text_lower)
    high_count = sum(1 for kw in high_keywords if kw in text_lower)
    medium_count = sum(1 for kw in medium_keywords if kw in text_lower)

    score = critical_count * 4 + high_count * 2 + medium_count
    if score >= 4 or critical_count >= 1:
        return "critical"
    if score >= 2 or high_count >= 1:
        return "high"
    if score >= 1 or medium_count >= 1:
        return "medium"
    return "low"


def _duplicate_priority_boost(duplicate_check: dict) -> str:
    count = duplicate_check.get("similar_nearby_count", 0)
    sim = duplicate_check.get("similarity_score", 0.0)
    strength = duplicate_check.get("cluster_strength", "low")

    if strength == "critical" or count >= 10:
        return "critical"
    if strength == "high" or (duplicate_check.get("is_duplicate") and sim >= 0.9):
        return "high"
    if strength == "medium" or count >= 3:
        return "medium"
    return "low"


def predict_priority(text: str, duplicate_check: dict | None = None) -> dict:
    text_level = _text_priority_score(text)
    dup_level = _duplicate_priority_boost(duplicate_check or {})

    final = text_level
    if PRIORITY_RANK[dup_level] > PRIORITY_RANK[final]:
        final = dup_level

    factors = []
    if duplicate_check:
        if duplicate_check.get("is_duplicate"):
            factors.append(f"Duplicate match ({duplicate_check.get('similarity_score', 0):.0%})")
        cnt = duplicate_check.get("similar_nearby_count", 0)
        if cnt >= 2:
            factors.append(f"{cnt} similar complaints nearby")

    return {
        "level": final,
        "confidence": 0.82 if factors else 0.75,
        "text_priority": text_level,
        "duplicate_priority": dup_level,
        "factors": factors,
    }
