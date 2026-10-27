"""Train and compare classic text classifiers on the ORR dataset (offline only)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from algorithms import keyword_router  # noqa: E402
from algorithms.embedding_router import EmbeddingCentroidRouter, EmbeddingKNNRouter  # noqa: E402
from algorithms.xgb_router import TfidfXGBRouter  # noqa: E402
from scripts._paths import ARTIFACTS_DIR, DATA_DIR  # noqa: E402


def _text(r: dict) -> str:
    return (r["title"] + " " + r["description"]).strip()


def _metrics(y_true: list[str], y_pred: list[str]) -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "n": len(y_true),
    }


def _train_pipeline(clf) -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95, sublinear_tf=True)),
            ("clf", clf),
        ]
    )


def main() -> None:
    path = DATA_DIR / "civic_routing_v1.json"
    records = json.loads(path.read_text(encoding="utf-8"))["records"]
    train = [r for r in records if r["split"] == "train"]
    val = [r for r in records if r["split"] == "val"]
    hold = [r for r in records if r["split"] == "holdout"]

    X_train = [_text(r) for r in train]
    y_train = [r["department_code"] for r in train]
    split_map = {
        "train": train,
        "validation": val,
        "holdout": hold,
    }

    xgb_model = TfidfXGBRouter()
    xgb_model.fit(X_train, y_train)

    print("Training embedding routers (downloads MiniLM on first run)...")
    emb_centroid = EmbeddingCentroidRouter()
    emb_centroid.fit(X_train, y_train)
    emb_knn = EmbeddingKNNRouter(k=5)
    emb_knn.fit(X_train, y_train)

    candidates: dict = {
        "keyword_router_v1": None,
        "tfidf_logistic_regression": _train_pipeline(
            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)
        ),
        "tfidf_linear_svc": _train_pipeline(LinearSVC(class_weight="balanced", random_state=42)),
        "tfidf_multinomial_nb": _train_pipeline(MultinomialNB()),
        "tfidf_xgboost": xgb_model,
        "embedding_centroid_minilm": emb_centroid,
        "embedding_knn5_minilm": emb_knn,
    }

    for name, pipe in candidates.items():
        if pipe is not None and name not in ("tfidf_xgboost", "embedding_centroid_minilm", "embedding_knn5_minilm"):
            pipe.fit(X_train, y_train)

    report: dict = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "department_code classification",
        "train_size": len(train),
        "note": "Offline lab only — production uses Gemini",
        "models": {},
    }

    for split_name, subset in split_map.items():
        if not subset:
            continue
        texts = [_text(r) for r in subset]
        truth = [r["department_code"] for r in subset]
        for name, pipe in candidates.items():
            if name not in report["models"]:
                report["models"][name] = {}
            if pipe is None:
                preds = [keyword_router.predict(t).department_code for t in texts]
            elif name == "tfidf_xgboost":
                preds = pipe.predict(texts)
            elif name.startswith("embedding_"):
                preds = pipe.predict_batch(texts)
            else:
                preds = list(pipe.predict(texts))
            report["models"][name][split_name] = _metrics(truth, preds)

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS_DIR / "model_comparison.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\nSaved -> {out}")

    print("\n=== Accuracy table (department routing) ===")
    print(f"{'Model':<32} {'Train':>8} {'Val':>8} {'Holdout':>8}")
    print("-" * 58)
    for name in candidates:
        m = report["models"][name]
        tr = m.get("train", {})
        va = m.get("validation", {})
        ho = m.get("holdout", {})
        print(
            f"{name:<32} "
            f"{tr.get('accuracy', 0)*100:7.2f}% "
            f"{va.get('accuracy', 0)*100:7.2f}% "
            f"{ho.get('accuracy', 0)*100:7.2f}%"
        )
    print("\nUse HOLDOUT column to pick the best model (not train).")


if __name__ == "__main__":
    main()
