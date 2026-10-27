# Dataset summary (for project report)

**Name:** Humanizr Civic Routing Lab (`humanizr_civic_routing_sim_v3`)  
**Purpose:** Supervised learning for **department routing** without using Gemini (isolated from production).

## Scale

| Metric | Value |
|--------|--------|
| Total labeled samples | **752** (regenerate: `python scripts/build_dataset.py`) |
| Train / validation / holdout | **564 / 100 / 88**, **stratified by department** |
| Rows per department | ~88–112 per class (balanced simulation) |
| Departments (classes) | 7 (PWD, SAN, WSD, ELEC, TNT, PAR, UNSUPPORTED) |
| With simulated photo | ~72% of rows |

## What each row contains

Citizen-style **title** and **description**, ground-truth **department_code** and **priority**, optional **image_path**, and split assignment for proper ML evaluation (train → tune → final test on holdout).

## How to cite in your report

> We built a simulated civic grievance corpus of 752 records aligned with Humanizr’s six routing departments. Models were trained on the training split, compared on validation, and final accuracy/F1 reported on a held-out test split. Production routing remains LLM-based (Gemini); this corpus evaluates classical ML baselines.

## Files

- `data/civic_routing_v1.json` — canonical dataset  
- `data/civic_routing_v1.csv` — same data for analysis  
- `artifacts/model_comparison.json` — benchmark results after `compare_models.py`
