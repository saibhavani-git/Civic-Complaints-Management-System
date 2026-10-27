"""CLI: predict department with offline algorithms."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms import keyword_router  # noqa: E402
from algorithms.tfidf_router import load, predict  # noqa: E402
from scripts._paths import ARTIFACTS_DIR  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("text", nargs="?", help="Complaint text")
    p.add_argument(
        "--algorithm",
        choices=("keyword", "tfidf", "xgboost", "embedding_centroid", "embedding_knn"),
        default="tfidf",
    )
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    text = args.text or sys.stdin.read()
    text = text.strip()
    if not text:
        raise SystemExit("Provide complaint text")

    if args.algorithm == "keyword":
        r = keyword_router.predict(text)
        out = {"department_code": r.department_code, "confidence": r.confidence, "algorithm": r.algorithm}
    elif args.algorithm == "xgboost":
        from algorithms.xgb_router import load as load_xgb

        path = ARTIFACTS_DIR / "department_tfidf_xgboost.joblib"
        if not path.exists():
            raise SystemExit("Train first: python scripts/train_xgboost.py")
        r = load_xgb(path).predict_one(text)
        out = {"department_code": r.department_code, "confidence": r.confidence, "algorithm": r.algorithm}
    elif args.algorithm in ("embedding_centroid", "embedding_knn"):
        from algorithms.embedding_router import load as load_emb

        fname = (
            "embedding_centroid_router.joblib"
            if args.algorithm == "embedding_centroid"
            else "embedding_knn_router.joblib"
        )
        path = ARTIFACTS_DIR / fname
        if not path.exists():
            raise SystemExit("Train first: python scripts/train_embeddings.py")
        r = load_emb(path).predict_one(text)
        out = {
            "department_code": r.department_code,
            "confidence": r.confidence,
            "match_percent": r.match_percent,
            "algorithm": r.algorithm,
        }
    else:
        path = ARTIFACTS_DIR / "department_tfidf_logreg.joblib"
        if not path.exists():
            raise SystemExit("Train first: python scripts/train_tfidf.py")
        r = predict(load(path), text)
        out = {
            "department_code": r.department_code,
            "confidence": r.confidence,
            "algorithm": r.algorithm,
            "top_alternatives": r.top_alternatives,
        }
    out["production_note"] = "Live app uses Gemini only — this is offline research"

    print(json.dumps(out, indent=2) if args.json else f"{out['department_code']} ({out['confidence']:.2f}) [{out['algorithm']}]")


if __name__ == "__main__":
    main()
