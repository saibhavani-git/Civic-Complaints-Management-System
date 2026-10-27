"""Fit embedding centroid + k-NN routers on train split (offline lab)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.embedding_router import EmbeddingCentroidRouter, EmbeddingKNNRouter, save  # noqa: E402
from scripts._paths import ARTIFACTS_DIR, DATA_DIR  # noqa: E402


def _text(row: dict) -> str:
    return (row["title"] + " " + row["description"]).strip()


def main() -> None:
    records = json.loads((DATA_DIR / "civic_routing_v1.json").read_text(encoding="utf-8"))["records"]
    train = [r for r in records if r["split"] == "train"]
    texts = [_text(r) for r in train]
    labels = [r["department_code"] for r in train]

    print(f"Encoding {len(texts)} train complaints (first run downloads MiniLM)...")
    centroid = EmbeddingCentroidRouter()
    centroid.fit(texts, labels)
    save(centroid, ARTIFACTS_DIR / "embedding_centroid_router.joblib")

    knn = EmbeddingKNNRouter(k=5)
    knn.fit(texts, labels)
    save(knn, ARTIFACTS_DIR / "embedding_knn_router.joblib")

    meta = {
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "encoder": "sentence-transformers/all-MiniLM-L6-v2",
        "train_size": len(train),
        "methods": ["centroid (mean vector per department)", "k-NN k=5 on stored train embeddings"],
        "artifacts": ["embedding_centroid_router.joblib", "embedding_knn_router.joblib"],
    }
    (ARTIFACTS_DIR / "embedding_training_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
