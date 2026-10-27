# ML guide (offline folder only)

**Gemini:** used in production — **do not change from here.**

This guide is only for `offline-routing-research/`.

## Problem

Given citizen **title + description**, predict:

- **department_code:** PWD, SAN, WSD, ELEC, TNT, PAR, or UNSUPPORTED  
- **priority:** low, medium, high, critical (second model)

## Dataset

`data/civic_routing_v1.json` — 408 records, id `ORR-NNNN`, train/val/holdout splits.

## Which model to try (without Gemini)

1. **Keyword router** — no ML; good first baseline.  
2. **TF-IDF + Logistic Regression** — recommended default; saved to `artifacts/`.  
3. **TF-IDF + Linear SVC** — often similar; compare with `compare_models.py`.  
4. **TF-IDF + Multinomial Naive Bayes** — fast; check macro-F1 on holdout.  
5. **TF-IDF + XGBoost** — gradient boosted trees on sparse text features; `pip install xgboost`, then `train_xgboost.py` / included in `compare_models.py`.

Images in the dataset are **not** used by current trainers (text-only). You can extend later with CLIP/CNN in this folder only.

## Commands

See [README.md](README.md) sections 2–3.
