# Dataset

- **Generate:** `python scripts/build_dataset.py` (520+ labeled samples, v3)
- **Primary key:** `id` (e.g. `ORR-0120`)
- **Report blurb:** see `docs/DATASET_SUMMARY.md`
- **Files:** `civic_routing_v1.json`, `civic_routing_v1.csv`, `images/*.svg`
- **Paraphrase stress test:** `paraphrase_oov_v1.json` (fresh wording; run `python scripts/evaluate_paraphrase_oov.py`)
