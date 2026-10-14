"""Rule-based civic category classification (MVP — upgrade to ML in production)."""

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "road": ["pothole", "road", "crack", "asphalt", "footpath", "pavement", "bridge"],
    "garbage": ["garbage", "waste", "trash", "dump", "litter", "sanitation", "bin"],
    "drainage": ["drain", "drainage", "block", "sewer", "flooding", "manhole"],
    "water": ["water", "leak", "pipeline", "tap", "supply", "contamination"],
    "street_light": ["streetlight", "street light", "lamp", "lighting", "dark"],
    "traffic": ["traffic", "signal", "parking", "accident", "congestion"],
    "parks": ["park", "tree", "garden", "playground", "green", "fallen"],
}


def classify_category(text: str) -> dict:
    lowered = text.lower()
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        scores[category] = sum(1 for kw in keywords if kw in lowered)

    best = max(scores, key=scores.get)
    best_score = scores[best]
    if best_score == 0:
        return {"category": "other", "confidence": 0.35, "alternatives": []}

    total = sum(scores.values()) or 1
    alts = sorted(
        [{"category": k, "score": v / total} for k, v in scores.items() if k != best and v > 0],
        key=lambda x: x["score"],
        reverse=True,
    )[:3]
    return {
        "category": best,
        "confidence": min(0.95, 0.45 + best_score * 0.12),
        "alternatives": alts,
    }
