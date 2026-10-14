# Humanizr AI Pipeline — Design, Data Model & Datasets

## Pipeline flow (production)

```
Citizen submits complaint + photos (Cloudinary URLs)
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│ 1. GEMINI ROUTING (6 departments only)                     │
│    app/ai/gemini_router.py + prompts/gemini_department.py  │
│    PWD, SAN, WSD, ELEC, TNT, PAR                           │
└─────────────────────────┬─────────────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────────────┐
│ 2. DUPLICATE DETECTION                                     │
│    Embedding similarity + geo radius (500m default)        │
│    Count similar_nearby_count (sim ≥ 0.75)                 │
│    Link duplicate_groups; inherit primary officer          │
└─────────────────────────┬─────────────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────────────┐
│ 5. PRIORITY                                                │
│    max(text urgency, duplicate cluster boost)              │
│    Many duplicates nearby → critical/high                  │
└─────────────────────────┬─────────────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────────────┐
│ 6. OFFICER ASSIGNMENT                                      │
│    Lowest active workload in department                    │
│    OR same officer as primary duplicate                    │
└───────────────────────────────────────────────────────────┘
```

Implementation: `backend/app/ai/pipeline.py`

---

## Data model (MongoDB)

### `complaints` (AI-relevant fields)

| Field | Description |
|-------|-------------|
| `images[].url` | Cloudinary URLs fed to vision router |
| `category` | Text category (road, garbage, …) |
| `department_id` | Routed department |
| `assigned_officer_id` | Workload-balanced assignee |
| `priority` | low / medium / high / critical |
| `duplicate_of_id` | Primary complaint if duplicate |
| `ai_metadata` | Full pipeline snapshot on document |

### `ai_results` (canonical AI output)

```javascript
{
  complaint_id: ObjectId,
  classification: { category, confidence, alternatives },
  priority: {
    level, confidence, text_priority, duplicate_priority, factors[]
  },
  duplicate_check: {
    is_duplicate, duplicate_of, similarity_score,
    similar_nearby_count, similar_matches[], cluster_strength, embedding
  },
  image_routing: {
    department_id, department_name, method, confidence, per_department_scores
  },
  routing: { routing_source, text_routing, image_routing, … },
  image_verification: { verified, confidence, message },
  model_versions: { embedder, image_department, priority, … },
  processing_time_ms: Number,
  created_at: Date
}
```

### `duplicate_groups`

Groups linked complaints with `similarity_score`, `primary_complaint_id`, `complaint_ids[]`.

---

## Models in use

| Step | Model | Hugging Face / Provider |
|------|--------|-------------------------|
| Text embeddings | `all-MiniLM-L6-v2` | sentence-transformers |
| Image → department | `openai/clip-vit-base-patch32` | transformers (zero-shot) |
| Image → department (optional) | `gemini-1.5-flash` | Google (multimodal) |
| Text → department | Cosine similarity vs dept keywords | Custom (no training) |
| Priority | Rules + duplicate cluster | Custom |
| Summarization | Gemini / OpenAI / truncate | Config-driven |

---

## Recommended public datasets (training & evaluation)

Use these to **fine-tune** CLIP or train a small classifier later. MVP uses zero-shot CLIP + your live Cloudinary data as continual improvement.

| Dataset | Use case | Link / notes |
|---------|----------|--------------|
| **TACO** | Trash / litter / illegal dumping → Sanitation | [TACO dataset](https://github.com/pedropro/TACO) |
| **RSDD / RDD2022** | Road damage, potholes → Public Works | [RDD2022](https://github.com/seunghoonpark/RoadDamageDetector) |
| **S2DS** (Street Surface Damage) | Pavement defects | Academic road damage sets |
| **NEU-DET** | Surface defects (general) | Metal/defect; transferable features |
| **Cityscapes** | Urban scenes | Segmentation; weak pretraining |
| **Open Images V7** | Generic objects | Filter: street, pothole, garbage, tree |
| **India-specific** | Limited open civic sets | **Build in-house** from Humanizr + officer labels |

### Recommended fine-tuning strategy (production)

1. **Phase A (now):** Zero-shot CLIP + Gemini vision + text fusion (no training).
2. **Phase B:** Export Cloudinary images + officer-confirmed department → CSV  
   `image_url, department_code, category, verified_by_officer`.
3. **Phase C:** Fine-tune CLIP head or train EfficientNet-B0 / MobileNet on your CSV (~500+ images per class minimum).
4. **Phase D:** Evaluate with macro-F1 per department; target ≥ 0.75 before auto-routing without review.

### Duplicate detection dataset

No single public “civic duplicate” set. Train/evaluate using:

- Synthetic pairs from your DB (same location + paraphrased descriptions).
- **STS Benchmark** style pairs for embedding threshold tuning.
- Geo-negative mining: nearby but different category → should **not** merge.

Thresholds (configurable in `backend/.env`):

- `DUPLICATE_SIMILARITY_THRESHOLD=0.85` — mark duplicate
- `SIMILAR_BAND=0.75` — count for cluster priority

---

## Priority rules (duplicate-aware)

| Condition | Priority boost |
|-----------|----------------|
| ≥10 similar within 500m, sim ≥ 0.8 | **critical** |
| ≥5 similar OR duplicate sim ≥ 0.92 | **high** |
| ≥3 similar OR duplicate flagged | **medium** |
| Text keywords (emergency, flood, …) | Can override to **critical** |

---

## Code map

| File | Role |
|------|------|
| `ai/gemini_router.py` | **Production** Gemini → 6 departments |
| `ai/prompts/gemini_department.py` | Routing prompt |
| `ai/departments_config.py` | PWD, SAN, WSD, ELEC, TNT, PAR |
| `ai/pipeline.py` | Orchestrator (Gemini → dupes → priority) |
| `ai/duplicate_detector.py` | Geo + embedding duplicates |
| `ai/priority_predictor.py` | Text + cluster priority |
| `research/simulation/` | Dataset + MiniLM/CLIP ensemble (demo only) |

Officer assignment is manual: **department admin** uses `POST /complaints/{id}/assign`.

---

## Environment

```env
GEMINI_API_KEY=          # required for production department routing
DUPLICATE_SIMILARITY_THRESHOLD=0.85
CLOUDINARY_*             # required for citizen photo uploads
```

First CLIP run downloads ~600MB model weights (cached by Hugging Face).
