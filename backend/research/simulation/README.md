# Simulation & multi-model research (Humanizr)

**Production complaints** use Gemini only (`app/ai/gemini_router.py` + `app/ai/pipeline.py`) over **six departments**: PWD, SAN, WSD, ELEC, TNT, PAR.

This folder is for **evaluation and demos**:

| Path | Purpose |
|------|---------|
| `data/simulated_classification_dataset.json` | 10 labeled samples with pre-recorded 3-model predictions |
| `models/model_ensemble.py` | Live comparison: Gemini + MiniLM + CLIP |
| `models/text_classifier.py` | MiniLM text router |
| `models/image_classifier.py` | CLIP / optional Gemini vision |
| `models/routing.py` | Text+image fusion helper (legacy experiments) |

API: `GET /api/v1/ai/sample-dataset`, `POST /api/v1/ai/simulation/classify` (staff only).
