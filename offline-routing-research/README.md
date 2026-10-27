# Offline routing research (isolated)

Try **non-Gemini** models on a civic routing dataset.  
**Humanizr production keeps using Gemini only** — nothing here is integrated with the Grievance project.

See [`ISOLATION.md`](ISOLATION.md).

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

## 2. Models you can use (without Gemini)

| Model | Type | Train? | File |
|-------|------|--------|------|
| **Keyword router** | Rules / keyword counts | No | `algorithms/keyword_router.py` |
| **TF-IDF + Logistic Regression** | Classic ML (main) | Yes | `scripts/train_tfidf.py` → `artifacts/department_tfidf_logreg.joblib` |
| **TF-IDF + Linear SVC** | Classic ML | Yes | `scripts/compare_models.py` |
| **TF-IDF + Multinomial Naive Bayes** | Classic ML | Yes | `scripts/compare_models.py` |
| **TF-IDF + XGBoost** | Gradient boosted trees on text features | Yes | `scripts/train_xgboost.py` → `artifacts/department_tfidf_xgboost.joblib` |

**Input to all text models:** `title` + `description` (images in the dataset are for future experiments; current trainers are **text-only**).

**Outputs:** predicted `department_code` (PWD, SAN, WSD, ELEC, TNT, PAR, UNSUPPORTED) and optional **priority** head (logistic regression on same features).

---

## 3. How to run (full workflow)

Use a **venv inside this folder only** (do not use the backend venv for deployment coupling — only convenience):

```powershell
cd offline-routing-research
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

**Step A — dataset (skip if `data/civic_routing_v1.json` exists):**

```powershell
python scripts/build_dataset.py
```

**Step B — train default models (department + priority):**

```powershell
python scripts/train_tfidf.py
```

**Step C — compare which classic model fits best (val + holdout):**

```powershell
python scripts/compare_models.py
```

Prints accuracy / macro-F1 and writes `artifacts/model_comparison.json`.

**Step D — try one complaint string:**

```powershell
python scripts/predict_cli.py "Traffic signal stuck on red near school"
python scripts/predict_cli.py "Garbage burning in the lane" --algorithm keyword
```

**Step E — evaluate saved TF-IDF models only:**

```powershell
python scripts/evaluate.py
```

---

## 4. Folder layout

```
offline-routing-research/
  data/              Dataset + images
  algorithms/        Model code (keyword, TF-IDF pipelines)
  scripts/           build, train, compare, predict, evaluate
  artifacts/         Trained .joblib + comparison JSON (generated)
  requirements.txt   pandas, scikit-learn, joblib only
```

---

## 5. What this does *not* do

- Does not call Google Gemini or change `backend/app/ai/gemini_router.py`
- Does not connect to MongoDB unless **you** run the optional export script manually
- Does not affect complaint submit, queue, or frontend

Use results for reports, thesis, or “what-if ML” — not for production routing.
