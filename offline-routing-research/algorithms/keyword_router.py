"""Rule-based department router — offline baseline only."""

from __future__ import annotations

from dataclasses import dataclass

# department_code -> keywords (lowercase)
KEYWORDS: dict[str, list[str]] = {
    "PWD": [
        "pothole", "road", "footpath", "pavement", "asphalt", "bridge", "flyover",
        "streetlight", "street light", "sinkhole", "speed breaker", "crack",
    ],
    "SAN": [
        "garbage", "waste", "trash", "bin", "sanitation", "dump", "sewer smell",
        "dead animal", "burning plastic", "litter",
    ],
    "WSD": [
        "water", "pipeline", "leak", "tap", "pressure", "contamination", "sediment",
        "burst pipe", "tanker", "drinking",
    ],
    "ELEC": [
        "power", "electricity", "transformer", "wire", "cable", "outage", "meter",
        "sparks", "voltage", "pole",
    ],
    "TNT": [
        "traffic", "signal", "junction", "parking", "bus stop", "congestion",
        "zebra", "gridlock", "ambulance lane",
    ],
    "PAR": [
        "park", "tree", "playground", "swing", "garden", "grass", "fountain",
        "recreation", "jogging",
    ],
    "UNSUPPORTED": [
        "police", "fir", "tax portal", "income tax", "flight", "airline",
        "school fee", "private school admission", "court", "lawyer",
    ],
}


@dataclass
class RoutingPrediction:
    department_code: str
    confidence: float
    algorithm: str = "keyword_v1"


def predict(text: str) -> RoutingPrediction:
    lowered = (text or "").lower()
    scores = {code: 0 for code in KEYWORDS}
    for code, words in KEYWORDS.items():
        for w in words:
            if w in lowered:
                scores[code] += 1

    best = max(scores, key=scores.get)
    best_score = scores[best]
    if best_score == 0:
        return RoutingPrediction("UNSUPPORTED", 0.35)

    total = sum(scores.values()) or 1
    conf = min(0.92, 0.4 + (best_score / total) * 0.5)
    return RoutingPrediction(best, conf)
