"""Compare keyword vs TF-IDF on val and holdout splits."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sklearn.metrics import accuracy_score, f1_score

from algorithms import keyword_router  # noqa: E402
from algorithms.tfidf_router import load, predict  # noqa: E402
from scripts._paths import ARTIFACTS_DIR, DATA_DIR  # noqa: E402


def _text(r: dict) -> str:
    return (r["title"] + " " + r["description"]).strip()


def _report(name: str, truth: list[str], preds: list[str]) -> None:
    acc = accuracy_score(truth, preds)
    f1 = f1_score(truth, preds, average="macro", zero_division=0)
    print(f"  {name}: accuracy={acc:.2%}  macro-F1={f1:.2%}  (n={len(truth)})")


def main() -> None:
    records = json.loads((DATA_DIR / "civic_routing_v1.json").read_text(encoding="utf-8"))["records"]

    for split in ("val", "holdout"):
        subset = [r for r in records if r["split"] == split]
        if not subset:
            continue
        texts = [_text(r) for r in subset]
        dept_truth = [r["department_code"] for r in subset]
        print(f"\n=== Department routing — {split} ===")
        kw = [keyword_router.predict(t).department_code for t in texts]
        _report("Keyword router", dept_truth, kw)

        model_path = ARTIFACTS_DIR / "department_tfidf_logreg.joblib"
        if model_path.exists():
            pipe = load(model_path)
            ml = [predict(pipe, t).department_code for t in texts]
            _report("TF-IDF + LogisticRegression", dept_truth, ml)
        else:
            print("  (Run scripts/train_tfidf.py first)")

    pri_path = ARTIFACTS_DIR / "priority_tfidf_logreg.joblib"
    if pri_path.exists():
        hold = [r for r in records if r["split"] == "holdout"]
        texts = [_text(r) for r in hold]
        truth = [r["priority"] for r in hold]
        pipe = load(pri_path)
        preds = [predict(pipe, t).department_code for t in texts]
        print("\n=== Priority (TF-IDF) — holdout ===")
        _report("Priority classifier", truth, preds)

    with_img = sum(1 for r in records if r.get("has_image"))
    print(f"\nDataset: {len(records)} rows, {with_img} with image_path (multimodal-ready)")


if __name__ == "__main__":
    main()
