def predict_priority(text: str) -> str:
    lowered = text.lower()
    if any(w in lowered for w in ["accident", "injury", "urgent", "critical", "electrocution"]):
        return "critical"
    if any(w in lowered for w in ["danger", "blocked", "overflow", "no water", "no power"]):
        return "high"
    if any(w in lowered for w in ["minor", "small", "slow"]):
        return "low"
    return "medium"
