"""Department classification using Sentence Transformers + cosine similarity."""

import logging
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from app.db.database import get_database

logger = logging.getLogger(__name__)

_model: Optional[SentenceTransformer] = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


async def classify_department(text: str) -> dict:
    from app.ai.departments_config import load_routing_departments

    db = get_database()
    departments = await load_routing_departments(db)

    if not departments:
        return {"department_id": None, "department_name": "Unclassified", "confidence": 0.0}

    model = _get_model()
    complaint_embedding = model.encode(text)

    best_score = -1.0
    best_dept = None

    for dept in departments:
        keywords = dept.get("keywords", [])
        dept_text = f"{dept['name']}. {dept.get('description', '')}. {', '.join(keywords)}"
        dept_embedding = model.encode(dept_text)
        similarity = float(np.dot(complaint_embedding, dept_embedding) / (
            np.linalg.norm(complaint_embedding) * np.linalg.norm(dept_embedding)
        ))
        if similarity > best_score:
            best_score = similarity
            best_dept = dept

    if best_dept:
        return {
            "department_id": str(best_dept["_id"]),
            "department_name": best_dept["name"],
            "department_code": best_dept.get("code"),
            "confidence": round(best_score, 3),
        }

    return {"department_id": None, "department_name": "Unclassified", "confidence": 0.0}
