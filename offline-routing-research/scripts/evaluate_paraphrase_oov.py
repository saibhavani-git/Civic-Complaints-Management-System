"""Compare TF-IDF+logreg vs embedding k-NN on paraphrase OOV test set."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline

from algorithms.embedding_router import EmbeddingKNNRouter  # noqa: E402
from scripts._paths import ARTIFACTS_DIR, DATA_DIR  # noqa: E402

WORD_RE = re.compile(r"[a-z]{3,}")


def _text(r: dict) -> str:
    return (r["title"] + " " + r["description"]).strip()


def _tokenize(text: str) -> list[str]:
    return WORD_RE.findall(text.lower())


def _build_orr_vocab(records: list[dict]) -> set[str]:
    vocab: set[str] = set()
    for r in records:
        vocab.update(_tokenize(_text(r)))
    return vocab


def _overlap_stats(texts: list[str], orr_vocab: set[str]) -> dict:
    per_text: list[dict] = []
    all_tokens: list[str] = []
    for t in texts:
        toks = _tokenize(t)
        all_tokens.extend(toks)
        in_db = [w for w in toks if w in orr_vocab]
        per_text.append(
            {
                "token_count": len(toks),
                "in_database_count": len(in_db),
                "in_database_ratio": (len(in_db) / len(toks)) if toks else 0.0,
                "in_database_words": sorted(set(in_db)),
            }
        )
    unique = set(all_tokens)
    in_db_unique = unique & orr_vocab
    return {
        "unique_tokens": len(unique),
        "unique_in_database": len(in_db_unique),
        "unique_oov_ratio": 1.0 - (len(in_db_unique) / len(unique)) if unique else 0.0,
        "per_record": per_text,
    }


def _train_tfidf(X_train: list[str], y_train: list[str]) -> Pipeline:
    pipe = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95, sublinear_tf=True)),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)),
        ]
    )
    pipe.fit(X_train, y_train)
    return pipe


def _metrics(name: str, truth: list[str], preds: list[str]) -> dict:
    return {
        "model": name,
        "accuracy": float(accuracy_score(truth, preds)),
        "macro_f1": float(f1_score(truth, preds, average="macro", zero_division=0)),
        "n": len(truth),
    }


def _misclassified(records: list[dict], truth: list[str], preds: list[str]) -> list[dict]:
    out = []
    for r, t, p in zip(records, truth, preds):
        if t != p:
            out.append({"id": r["id"], "truth": t, "pred": p, "text": _text(r)[:200]})
    return out


def main() -> None:
    orr_path = DATA_DIR / "civic_routing_v1.json"
    oov_path = DATA_DIR / "paraphrase_oov_v1.json"
    if not oov_path.exists():
        raise SystemExit("Missing data/paraphrase_oov_v1.json")

    orr = json.loads(orr_path.read_text(encoding="utf-8"))["records"]
    oov_blob = json.loads(oov_path.read_text(encoding="utf-8"))
    oov = oov_blob["records"]

    train = [r for r in orr if r["split"] == "train"]
    hold = [r for r in orr if r["split"] == "holdout"]

    X_train = [_text(r) for r in train]
    y_train = [r["department_code"] for r in train]

    oov_texts = [_text(r) for r in oov]
    oov_truth = [r["department_code"] for r in oov]

    orr_vocab = _build_orr_vocab(orr)
    overlap = _overlap_stats(oov_texts, orr_vocab)

    print("Training TF-IDF + LogisticRegression on ORR train split...")
    tfidf = _train_tfidf(X_train, y_train)

    print("Training embedding k-NN (MiniLM, k=5) on ORR train split...")
    knn = EmbeddingKNNRouter(k=5)
    knn.fit(X_train, y_train)

    sets = {
        "orr_holdout_baseline": (hold, [_text(r) for r in hold], [r["department_code"] for r in hold]),
        "paraphrase_oov_v1": (oov, oov_texts, oov_truth),
    }

    report: dict = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "department_code classification",
        "train_size": len(train),
        "note": "Paraphrase set uses fresh wording; overlap stats vs full ORR vocabulary.",
        "vocabulary_overlap": overlap,
        "evaluations": {},
    }

    print("\n=== Vocabulary overlap (paraphrase vs ORR corpus) ===")
    print(
        f"  Unique tokens in paraphrase set: {overlap['unique_tokens']}  "
        f"| already in ORR: {overlap['unique_in_database']}  "
        f"| OOV token ratio: {overlap['unique_oov_ratio']:.1%}"
    )

    for split_name, (recs, texts, truth) in sets.items():
        tfidf_pred = list(tfidf.predict(texts))
        knn_pred = knn.predict_batch(texts)
        report["evaluations"][split_name] = {
            "tfidf_logistic_regression": _metrics("tfidf_logistic_regression", truth, tfidf_pred),
            "embedding_knn5_minilm": _metrics("embedding_knn5_minilm", truth, knn_pred),
            "tfidf_errors": _misclassified(recs, truth, tfidf_pred),
            "knn_errors": _misclassified(recs, truth, knn_pred),
        }
        if split_name == "paraphrase_oov_v1":
            labels = sorted(set(truth))
            report["evaluations"][split_name]["tfidf_confusion"] = confusion_matrix(
                truth, tfidf_pred, labels=labels
            ).tolist()
            report["evaluations"][split_name]["knn_confusion"] = confusion_matrix(
                truth, knn_pred, labels=labels
            ).tolist()

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS_DIR / "paraphrase_oov_eval.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n=== Accuracy (department routing) ===")
    print(f"{'Split':<28} {'TF-IDF+LR':>12} {'Emb k-NN':>12}")
    print("-" * 54)
    for split_name in sets:
        ev = report["evaluations"][split_name]
        ta = ev["tfidf_logistic_regression"]["accuracy"] * 100
        ka = ev["embedding_knn5_minilm"]["accuracy"] * 100
        print(f"{split_name:<28} {ta:11.2f}% {ka:11.2f}%")

    oov_ev = report["evaluations"]["paraphrase_oov_v1"]
    print(f"\nParaphrase macro-F1: TF-IDF {oov_ev['tfidf_logistic_regression']['macro_f1']:.2%}  "
          f"| k-NN {oov_ev['embedding_knn5_minilm']['macro_f1']:.2%}")
    print(f"\nSaved -> {out}")
    if oov_ev["tfidf_errors"]:
        print("\nSample TF-IDF mistakes (first 5):")
        for e in oov_ev["tfidf_errors"][:5]:
            print(f"  {e['id']}: truth={e['truth']} pred={e['pred']}")
    if oov_ev["knn_errors"]:
        print("\nSample k-NN mistakes (first 5):")
        for e in oov_ev["knn_errors"][:5]:
            print(f"  {e['id']}: truth={e['truth']} pred={e['pred']}")


if __name__ == "__main__":
    main()
