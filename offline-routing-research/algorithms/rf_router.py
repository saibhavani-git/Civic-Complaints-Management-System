"""TF-IDF + Random Forest — offline department router (not production)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline


@dataclass
class RoutingPrediction:
    department_code: str
    confidence: float
    algorithm: str = "tfidf_random_forest_v1"


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95, sublinear_tf=True),
            ),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=200,
                    max_depth=None,
                    min_samples_leaf=1,
                    class_weight="balanced_subsample",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )


class TfidfRandomForestRouter:
    def __init__(self) -> None:
        self.pipe = build_pipeline()

    def fit(self, texts: list[str], labels: list[str]) -> None:
        self.pipe.fit(texts, labels)

    def predict(self, texts: list[str]) -> list[str]:
        return list(self.pipe.predict(texts))

    def predict_one(self, text: str) -> RoutingPrediction:
        dept = self.pipe.predict([text])[0]
        clf = self.pipe.named_steps["clf"]
        conf = 0.5
        if hasattr(clf, "predict_proba"):
            probs = clf.predict_proba(self.pipe.named_steps["tfidf"].transform([text]))[0]
            conf = float(max(probs))
        return RoutingPrediction(str(dept), conf)


def save(pipe: Pipeline, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, path)


def load(path: Path) -> Pipeline:
    return joblib.load(path)
