# Offline model code

| File | Algorithm |
|------|-----------|
| `keyword_router.py` | Rule / keyword scoring (no training) |
| `tfidf_router.py` | TF-IDF + Logistic Regression pipeline |
| `xgb_router.py` | TF-IDF + XGBoost |
| `rf_router.py` | TF-IDF + Random Forest |
| `embedding_router.py` | MiniLM + centroid or k-NN |

**Run and compare everything:** [../MODELS_RUN_AND_COMPARE.md](../MODELS_RUN_AND_COMPARE.md)

Production Humanizr routing: **Gemini only** (outside this folder).
