"""Duplicate detection — semantic similarity + geo radius + cluster density for priority."""

import logging

import numpy as np
from bson import ObjectId

from app.ai.classifier import _get_model
from app.config import get_settings
from app.db.database import get_database

logger = logging.getLogger(__name__)

SIMILAR_BAND = 0.75  # count complaints above this as "similar cluster"


async def detect_duplicate(
    text: str,
    current_complaint_id: str,
    location: dict,
    radius_km: float = 0.5,
) -> dict:
    settings = get_settings()
    model = _get_model()
    embedding = model.encode(text).tolist()

    db = get_database()
    lat, lng = location.get("lat", 0), location.get("lng", 0)

    nearby = db.complaints.find(
        {
            "_id": {"$ne": ObjectId(current_complaint_id)},
            "status": {"$nin": ["closed", "rejected"]},
            "location": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [lng, lat]},
                    "$maxDistance": radius_km * 1000,
                }
            },
        }
    ).limit(80)

    best_similarity = 0.0
    duplicate_of = None
    similar_nearby_count = 0
    similar_matches: list[dict] = []

    async for doc in nearby:
        existing_embedding = doc.get("ai_metadata", {}).get("embedding")
        if existing_embedding:
            sim = _cosine_similarity(embedding, existing_embedding)
        else:
            existing_text = f"{doc.get('title', '')}. {doc.get('description', '')}"
            existing_emb = model.encode(existing_text).tolist()
            sim = _cosine_similarity(embedding, existing_emb)

        if sim >= SIMILAR_BAND:
            similar_nearby_count += 1
            similar_matches.append(
                {
                    "complaint_id": str(doc["_id"]),
                    "human_id": doc.get("complaint_id"),
                    "similarity": round(sim, 3),
                }
            )

        if sim > best_similarity:
            best_similarity = sim
            duplicate_of = doc["_id"]

    is_duplicate = best_similarity >= settings.DUPLICATE_SIMILARITY_THRESHOLD

    return {
        "is_duplicate": is_duplicate,
        "duplicate_of": str(duplicate_of) if is_duplicate and duplicate_of else None,
        "similarity_score": round(best_similarity, 3),
        "similar_nearby_count": similar_nearby_count,
        "similar_matches": similar_matches[:10],
        "embedding": embedding,
        "cluster_strength": _cluster_strength(similar_nearby_count, best_similarity),
    }


def _cluster_strength(count: int, max_sim: float) -> str:
    if count >= 10 and max_sim >= 0.8:
        return "critical"
    if count >= 5 or max_sim >= 0.92:
        return "high"
    if count >= 2 or max_sim >= 0.85:
        return "medium"
    return "low"


def _cosine_similarity(a: list, b: list) -> float:
    a_arr, b_arr = np.array(a), np.array(b)
    dot = np.dot(a_arr, b_arr)
    norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    return float(dot / norm) if norm > 0 else 0.0
