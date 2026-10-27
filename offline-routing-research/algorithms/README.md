# Offline models (not Gemini)

| Name | Algorithm | When to use |
|------|-----------|-------------|
| `keyword_router.py` | Keyword scoring | Fast baseline, no training |
| `tfidf_router.py` | TF-IDF + LogisticRegression | Default ML router after `train_tfidf.py` |

Run **`python scripts/compare_models.py`** to see how Logistic Regression, Linear SVC, and Multinomial Naive Bayes compare on your splits.

Production Humanizr: **Gemini only** (outside this folder).
