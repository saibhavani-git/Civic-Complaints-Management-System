"""Train TF-IDF + XGBoost department model (offline lab only)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.xgb_router import TfidfXGBRouter, save  # noqa: E402
from scripts._paths import ARTIFACTS_DIR, DATA_DIR  # noqa: E402


def _text(row: dict) -> str:
    return (row["title"] + " " + row["description"]).strip()


def main() -> None:
    records = json.loads((DATA_DIR / "civic_routing_v1.json").read_text(encoding="utf-8"))["records"]
    train_rows = [r for r in records if r["split"] == "train"]
    texts = [_text(r) for r in train_rows]
    labels = [r["department_code"] for r in train_rows]

    model = TfidfXGBRouter()
    model.fit(texts, labels)
    out = ARTIFACTS_DIR / "department_tfidf_xgboost.joblib"
    save(model, out)

    meta = {
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "algorithm": "TfidfVectorizer + XGBClassifier (multi:softmax)",
        "train_size": len(train_rows),
        "artifact": out.name,
        "production_note": "Gemini used in production — this is isolated research",
    }
    (ARTIFACTS_DIR / "xgboost_training_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
