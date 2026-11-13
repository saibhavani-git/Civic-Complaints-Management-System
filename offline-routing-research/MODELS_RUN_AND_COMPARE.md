# How to run and compare offline routing models

Step-by-step guide for **`offline-routing-research/`** only.  
The live Humanizr app uses **Gemini** — these models are for experiments and reports.

Conceptual overview: [ML_GUIDE.md](ML_GUIDE.md) · Paraphrase stress test: [docs/PARAPHRASE_OOV_EVAL.md](docs/PARAPHRASE_OOV_EVAL.md)

---

## 1. One-time setup

From repo root:

```powershell
cd offline-routing-research
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

**First embedding run** downloads `all-MiniLM-L6-v2` (~90 MB). Needs network once.

**Dataset** (already in repo): `data/civic_routing_v1.json` — 752 rows, splits `train` (564) / `val` (100) / `holdout` (88).

Optional regenerate:

```powershell
python scripts/build_dataset.py
```

---

## 2. Models included in the comparison

| Key in reports | What it is | Trained by |
|----------------|------------|------------|
| `keyword_router_v1` | Keyword counts per department | No training |
| `tfidf_logistic_regression` | TF-IDF + logistic regression | `compare_models.py` or `train_tfidf.py` |
| `tfidf_linear_svc` | TF-IDF + linear SVC | `compare_models.py` |
| `tfidf_multinomial_nb` | TF-IDF + Naive Bayes | `compare_models.py` |
| `tfidf_xgboost` | TF-IDF + XGBoost | `compare_models.py` or `train_xgboost.py` |
| `tfidf_random_forest` | TF-IDF + Random Forest (200 trees) | `compare_models.py` or `train_rf.py` |
| `embedding_centroid_minilm` | MiniLM embeddings + department centroids | `compare_models.py` or `train_embeddings.py` |
| `embedding_knn5_minilm` | MiniLM + k=5 nearest neighbors | `compare_models.py` or `train_embeddings.py` |

**Input:** `title` + `description` (text only).  
**Label:** `department_code` (PWD, SAN, WSD, ELEC, TNT, PAR, UNSUPPORTED).

---

## 3. Compare all models (main command)

Trains each model on the **train** split and scores **train**, **validation**, and **holdout**:

```powershell
.\.venv\Scripts\activate
python scripts/compare_models.py
```

**What you get:**

1. **Printed table** — accuracy % for Train / Val / Holdout  
2. **`artifacts/model_comparison.json`** — full metrics (accuracy, macro-F1, n)

**Which column to trust:** **Holdout** (88 samples). Do not pick a model using train accuracy alone.

Example table (your numbers may vary slightly after re-run):

```text
Model                                 Train      Val  Holdout
------------------------------------------------------------
keyword_router_v1                    72.87%   73.00%   68.18%
tfidf_logistic_regression           100.00%  100.00%  100.00%
tfidf_random_forest                 100.00%  100.00%  100.00%
tfidf_xgboost                       100.00%   99.00%   96.59%
embedding_centroid_minilm            93.79%   90.00%   87.50%
embedding_knn5_minilm               100.00%  100.00%  100.00%
```

---

## 4. Honest test: paraphrase / new wording

ORR holdout reuses similar phrases as train, so scores can look “too perfect.”  
Use the **paraphrase OOV** set (`data/paraphrase_oov_v1.json`, 70 rows, fresh vocabulary):

```powershell
python scripts/evaluate_paraphrase_oov.py
```

Writes **`artifacts/paraphrase_oov_eval.json`**.  
Compares **TF-IDF + LR**, **TF-IDF + Random Forest**, and **embedding k-NN** on:

- ORR holdout (baseline)
- Paraphrase OOV (harder)

Use this in your report alongside `compare_models.py`.

---

## 5. Train and save individual models

| Goal | Command | Artifact |
|------|---------|----------|
| Default TF-IDF + logreg (dept + priority) | `python scripts/train_tfidf.py` | `department_tfidf_logreg.joblib`, `priority_tfidf_logreg.joblib` |
| XGBoost | `python scripts/train_xgboost.py` | `department_tfidf_xgboost.joblib` |
| Random Forest | `python scripts/train_rf.py` | `department_tfidf_random_forest.joblib` |
| Embeddings (centroid + k-NN) | `python scripts/train_embeddings.py` | `embedding_centroid_router.joblib`, `embedding_knn_router.joblib` |

Metadata JSON files are written under `artifacts/` when applicable.

**Evaluate saved TF-IDF logreg only** (val + holdout):

```powershell
python scripts/evaluate.py
```

---

## 6. Predict one complaint (CLI)

After training the artifact you need:

```powershell
# Default: TF-IDF + logistic regression
python scripts/predict_cli.py "Overflowing garbage near school gate"

python scripts/predict_cli.py "Traffic signal stuck on red" --algorithm keyword
python scripts/predict_cli.py "Traffic signal stuck on red" --algorithm tfidf
python scripts/predict_cli.py "Traffic signal stuck on red" --algorithm xgboost
python scripts/predict_cli.py "Traffic signal stuck on red" --algorithm random_forest
python scripts/predict_cli.py "Refuse sacks ruptured on sidewalk" --algorithm embedding_knn
python scripts/predict_cli.py "Refuse sacks ruptured on sidewalk" --algorithm embedding_centroid

# JSON output
python scripts/predict_cli.py "Pothole on main road" --algorithm tfidf --json
```

| `--algorithm` | Requires |
|---------------|----------|
| `keyword` | nothing |
| `tfidf` | `train_tfidf.py` |
| `xgboost` | `train_xgboost.py` |
| `random_forest` | `train_rf.py` |
| `embedding_centroid` | `train_embeddings.py` |
| `embedding_knn` | `train_embeddings.py` |

---

## 7. Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: sklearn` | Activate `.venv` and `pip install -r requirements.txt` |
| `ModuleNotFoundError: sentence_transformers` | Same; first compare run needs download |
| `Train first: ...` from predict_cli | Run the matching `train_*.py` script |
| Compare is slow | Normal: embeddings + Random Forest on 564 train rows |
| 100% on holdout but bad on paraphrase | Expected on simulated data — cite paraphrase OOV in report |

---

## 8. Suggested workflow for a project report

1. `python scripts/compare_models.py` → table + `model_comparison.json`  
2. `python scripts/evaluate_paraphrase_oov.py` → generalization story  
3. `predict_cli.py` with **template** vs **paraphrase** text for demo screenshots  
4. State clearly: **production = Gemini**; offline winners = e.g. logreg + embedding k-NN on ORR holdout, k-NN ahead on paraphrase OOV  

---

## 9. File reference

| Path | Purpose |
|------|---------|
| `scripts/compare_models.py` | Train all + compare splits |
| `scripts/evaluate_paraphrase_oov.py` | LR vs RF vs k-NN on paraphrases |
| `scripts/predict_cli.py` | Single-text prediction |
| `scripts/train_tfidf.py` | Save logreg pipelines |
| `scripts/train_xgboost.py` | Save XGBoost |
| `scripts/train_rf.py` | Save Random Forest |
| `scripts/train_embeddings.py` | Save embedding routers |
| `artifacts/model_comparison.json` | Latest full comparison |
| `artifacts/paraphrase_oov_eval.json` | Latest paraphrase eval |
