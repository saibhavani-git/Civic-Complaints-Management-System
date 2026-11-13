# Offline routing research (isolated)

Try **non-Gemini** models on a civic routing dataset.  
**Humanizr production keeps using Gemini only** — nothing here is integrated with the Grievance project.

See [`ISOLATION.md`](ISOLATION.md).

**How to run models and compare accuracy:** **[MODELS_RUN_AND_COMPARE.md](MODELS_RUN_AND_COMPARE.md)** ← start here for commands and benchmarks.

---

## 1. Dataset (already in repo)

| Item | Location |
|------|----------|
| **752 rows**, ids `ORR-0001` … `ORR-0752` | `data/civic_routing_v1.json` |
| Spreadsheet-friendly export | `data/civic_routing_v1.csv` |
| Simulated complaint photos (~72% of rows) | `data/images/*.svg` |

**Columns:** `id`, `title`, `description`, `department_code` (label), `category`, `priority`, `split` (`train` / `val` / `holdout`), `has_image`, `image_path`, `image_caption`.

**Regenerate (optional):**

```powershell
cd offline-routing-research
python scripts/build_dataset.py
```

---

## 2. Models (summary)

Keyword baseline, TF-IDF + (LogReg, SVC, Naive Bayes, XGBoost, **Random Forest**), and **MiniLM embeddings** (centroid + k-NN).  
Full list, train commands, and compare workflow: **[MODELS_RUN_AND_COMPARE.md](MODELS_RUN_AND_COMPARE.md)**.

Quick compare:

```powershell
cd offline-routing-research
.\.venv\Scripts\activate
python scripts/compare_models.py
```

---

## 4. Folder layout

```
offline-routing-research/
  data/              Dataset + images
  algorithms/        Model code (keyword, TF-IDF pipelines)
  scripts/           build, train, compare, predict, evaluate
  artifacts/         Trained .joblib + comparison JSON (generated)
  requirements.txt   sklearn, xgboost, sentence-transformers, …
  MODELS_RUN_AND_COMPARE.md   Run / compare guide
```

---

## 5. What this does *not* do

- Does not call Google Gemini or change `backend/app/ai/gemini_router.py`
- Does not connect to MongoDB unless **you** run the optional export script manually
- Does not affect complaint submit, queue, or frontend

Use results for reports, thesis, or “what-if ML” — not for production routing.
