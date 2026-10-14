CATEGORY_KEYWORDS = {
    "road": ["pothole", "road", "crack", "asphalt"],
    "garbage": ["garbage", "waste", "trash", "dump"],
    "drainage": ["drain", "drainage", "sewer", "flooding"],
    "water": ["water", "leak", "pipeline", "tap"],
    "street_light": ["streetlight", "street light", "lamp"],
    "traffic": ["traffic", "signal", "parking"],
    "parks": ["park", "tree", "garden", "playground"],
}


def classify_category(text: str) -> dict:
    lowered = text.lower()
    scores = {k: sum(1 for kw in v if kw in lowered) for k, v in CATEGORY_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return {"category": "other", "confidence": 0.35}
    return {"category": best, "confidence": min(0.9, 0.5 + scores[best] * 0.1)}
