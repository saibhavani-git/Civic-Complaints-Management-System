"""Train TF-IDF classifiers (department + priority); saves to artifacts/."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.tfidf_router import save, train  # noqa: E402
from scripts._paths import ARTIFACTS_DIR, DATA_DIR  # noqa: E402


def _text(row: dict) -> str:
    return (row["title"] + " " + row["description"]).strip()


def main() -> None:
    path = DATA_DIR / "civic_routing_v1.json"
    if not path.exists():
        raise SystemExit("Run scripts/build_dataset.py first")

    records = json.loads(path.read_text(encoding="utf-8"))["records"]
    train_rows = [r for r in records if r["split"] == "train"]

    dept_pipe = train([_text(r) for r in train_rows], [r["department_code"] for r in train_rows])
    pri_pipe = train([_text(r) for r in train_rows], [r["priority"] for r in train_rows])

    save(dept_pipe, ARTIFACTS_DIR / "department_tfidf_logreg.joblib")
    save(pri_pipe, ARTIFACTS_DIR / "priority_tfidf_logreg.joblib")

    meta = {
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "algorithm": "TfidfVectorizer(1-2 grams) + LogisticRegression(balanced)",
        "train_size": len(train_rows),
        "targets": ["department_code", "priority"],
        "features": "title + description (text only; image_path stored for future multimodal)",
        "artifacts": {
            "department": "department_tfidf_logreg.joblib",
            "priority": "priority_tfidf_logreg.joblib",
        },
        "production_note": "Live app uses Gemini only",
    }
    (ARTIFACTS_DIR / "training_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
