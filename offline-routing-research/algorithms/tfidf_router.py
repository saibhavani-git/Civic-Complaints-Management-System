"""TF-IDF + logistic regression — offline trained router."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


@dataclass
class RoutingPrediction:
    department_code: str
    confidence: float
    algorithm: str = "tfidf_logreg_v1"
    top_alternatives: list[tuple[str, float]] | None = None


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95, sublinear_tf=True),
            ),
            (
                "clf",
                LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42),
            ),
        ]
    )


def train(texts: list[str], labels: list[str]) -> Pipeline:
    pipe = build_pipeline()
    pipe.fit(texts, labels)
    return pipe


def save(pipe: Pipeline, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, path)


def load(path: Path) -> Pipeline:
    return joblib.load(path)


def predict(pipe: Pipeline, text: str) -> RoutingPrediction:
    dept = pipe.predict([text])[0]
    clf = pipe.named_steps["clf"]
    conf = 0.5
    alts: list[tuple[str, float]] = []
    if hasattr(clf, "predict_proba"):
        probs = pipe.predict_proba([text])[0]
        classes = list(clf.classes_)
        pairs = sorted(zip(classes, probs), key=lambda x: -x[1])
        conf = float(pairs[0][1])
        alts = [(c, float(p)) for c, p in pairs[1:4]]
    return RoutingPrediction(str(dept), conf, top_alternatives=alts)
