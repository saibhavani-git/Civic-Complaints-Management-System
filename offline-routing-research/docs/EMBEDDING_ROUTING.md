# Embedding-based routing (idea → how it works)

## What you described

1. Turn each complaint (`title` + `description`) into a **dense vector embedding** (meaning, not raw word counts).
2. **Store** those vectors with the correct **department label** (from the dataset).
3. When a **new** complaint arrives, embed it and compare (**cosine similarity**) to stored vectors.
4. Route to the department with the **best match** (or nearest neighbors’ vote), optionally with a **minimum similarity** or confidence threshold → else UNSUPPORTED.

That is a standard **memory-based / retrieval** classifier. It is **much stronger than keyword frequency alone**, because “pothole”, “road crater”, and “broken carriageway” can sit close in vector space even if they share few words.

## How this compares (honest)

| Approach | Idea | Weakness |
|----------|------|----------|
| Keyword / word counts | Count hits per department | Misses paraphrases; **weakest** baseline |
| TF-IDF + logistic regression | Weighted word n-grams + learned linear boundaries | Fast; needs enough text; no deep “meaning” |
| **Embedding + similarity (your idea)** | Semantic vectors + nearest match / centroid | Needs good encoder; memory grows with data; threshold tuning |
| XGBoost on TF-IDF | Non-linear splits on sparse text features | Can overfit small/simulated data |
| **Gemini (production)** | LLM + optional images + policy | Not replaced by this lab |

We implement **two embedding variants** offline:

1. **Centroid routing** — one average embedding per department on the train split; new text → highest cosine to a centroid.
2. **k-NN routing** — keep all train embeddings; new text → **k=5** nearest neighbors → majority department vote.

**Encoder:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim, runs locally in this folder only).

## What gets saved

`artifacts/embedding_router.joblib` — encoder name, train embeddings (for k-NN), centroids, labels, k.

## Commands

```powershell
pip install -r requirements.txt
python scripts/train_embeddings.py
python scripts/compare_models.py   # includes embedding_centroid + embedding_knn
```

Use the **holdout** column in the printed table to judge models (same as TF-IDF / XGBoost).
