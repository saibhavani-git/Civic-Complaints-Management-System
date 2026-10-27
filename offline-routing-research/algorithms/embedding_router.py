"""Semantic embedding routers — cosine similarity to stored train vectors (offline only)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np


DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@dataclass
class RoutingPrediction:
    department_code: str
    confidence: float
    algorithm: str
    match_percent: float  # top cosine similarity as 0–100 style score


def _encode(model, texts: list[str]) -> np.ndarray:
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(vectors, dtype=np.float32)


class EmbeddingCentroidRouter:
    """Average train embedding per department; predict = argmax cosine to centroids."""

    algorithm = "embedding_centroid_minilm"

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self.model_name = model_name
        self._model = None
        self.centroids: dict[str, np.ndarray] = {}
        self.departments: list[str] = []

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def fit(self, texts: list[str], labels: list[str]) -> None:
        model = self._get_model()
        emb = _encode(model, texts)
        by_dept: dict[str, list[np.ndarray]] = {}
        for vec, lab in zip(emb, labels):
            by_dept.setdefault(lab, []).append(vec)
        self.departments = sorted(by_dept.keys())
        self.centroids = {d: np.mean(np.stack(vs), axis=0) for d, vs in by_dept.items()}
        for d in self.centroids:
            n = np.linalg.norm(self.centroids[d])
            if n > 0:
                self.centroids[d] = self.centroids[d] / n

    def predict_batch(self, texts: list[str]) -> list[str]:
        model = self._get_model()
        q = _encode(model, texts)
        preds = []
        dept_list = self.departments
        cent_mat = np.stack([self.centroids[d] for d in dept_list])
        for vec in q:
            sims = cent_mat @ vec
            preds.append(dept_list[int(np.argmax(sims))])
        return preds

    def predict_one(self, text: str) -> RoutingPrediction:
        model = self._get_model()
        vec = _encode(model, [text])[0]
        cent_mat = np.stack([self.centroids[d] for d in self.departments])
        sims = cent_mat @ vec
        idx = int(np.argmax(sims))
        conf = float(sims[idx])
        return RoutingPrediction(
            self.departments[idx],
            conf,
            self.algorithm,
            match_percent=round(max(0.0, conf) * 100, 2),
        )


class EmbeddingKNNRouter:
    """Store all train embeddings; k-NN majority vote (cosine = dot on normalized vectors)."""

    algorithm = "embedding_knn5_minilm"

    def __init__(self, model_name: str = DEFAULT_MODEL, k: int = 5) -> None:
        self.model_name = model_name
        self.k = k
        self._model = None
        self.train_emb: np.ndarray | None = None
        self.train_labels: list[str] = []

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def fit(self, texts: list[str], labels: list[str]) -> None:
        model = self._get_model()
        self.train_emb = _encode(model, texts)
        self.train_labels = list(labels)

    def predict_batch(self, texts: list[str]) -> list[str]:
        assert self.train_emb is not None
        model = self._get_model()
        q = _encode(model, texts)
        preds = []
        k = min(self.k, len(self.train_labels))
        for vec in q:
            sims = self.train_emb @ vec
            top = np.argpartition(-sims, k - 1)[:k]
            votes: dict[str, int] = {}
            for i in top:
                lab = self.train_labels[int(i)]
                votes[lab] = votes.get(lab, 0) + 1
            preds.append(max(votes, key=votes.get))
        return preds

    def predict_one(self, text: str) -> RoutingPrediction:
        assert self.train_emb is not None
        model = self._get_model()
        vec = _encode(model, [text])[0]
        sims = self.train_emb @ vec
        k = min(self.k, len(self.train_labels))
        top = np.argpartition(-sims, k - 1)[:k]
        top_sims = sims[top]
        votes: dict[str, int] = {}
        for i in top:
            lab = self.train_labels[int(i)]
            votes[lab] = votes.get(lab, 0) + 1
        best_dept = max(votes, key=votes.get)
        conf = float(np.mean(top_sims))
        return RoutingPrediction(
            best_dept,
            conf,
            self.algorithm,
            match_percent=round(max(0.0, conf) * 100, 2),
        )


def save(obj: EmbeddingCentroidRouter | EmbeddingKNNRouter, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(obj, path)


def load(path: Path) -> EmbeddingCentroidRouter | EmbeddingKNNRouter:
    return joblib.load(path)
