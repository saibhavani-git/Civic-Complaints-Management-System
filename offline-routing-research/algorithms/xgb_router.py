"""TF-IDF + XGBoost — offline department router (not production)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier


@dataclass
class RoutingPrediction:
    department_code: str
    confidence: float
    algorithm: str = "tfidf_xgboost_v1"


class TfidfXGBRouter:
    """Sparse TF-IDF features + gradient boosted trees."""

    def __init__(self) -> None:
        self.tfidf = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,
        )
        self.label_encoder = LabelEncoder()
        self.clf = XGBClassifier(
            objective="multi:softmax",
            max_depth=6,
            n_estimators=250,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            eval_metric="mlogloss",
        )

    def fit(self, texts: list[str], labels: list[str]) -> None:
        self.label_encoder.fit(labels)
        X = self.tfidf.fit_transform(texts)
        y = self.label_encoder.transform(labels)
        self.clf.fit(X, y)

    def predict(self, texts: list[str]) -> list[str]:
        X = self.tfidf.transform(texts)
        idx = self.clf.predict(X)
        return list(self.label_encoder.inverse_transform(idx.astype(int)))

    def predict_one(self, text: str) -> RoutingPrediction:
        code = self.predict([text])[0]
        conf = 0.5
        X = self.tfidf.transform([text])
        if hasattr(self.clf, "predict_proba"):
            probs = self.clf.predict_proba(X)[0]
            conf = float(probs.max())
        return RoutingPrediction(code, conf)


def save(model: TfidfXGBRouter, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load(path: Path) -> TfidfXGBRouter:
    return joblib.load(path)
