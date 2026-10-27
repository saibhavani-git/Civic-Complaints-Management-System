# Paraphrase / OOV evaluation

## Why this exists

The main ORR holdout reuses the same phrasing patterns as train (location boilerplate, shared civic terms). Both TF-IDF and embedding k-NN scored **100%** there, which does not tell you which model generalizes when citizens use **different words**.

`data/paraphrase_oov_v1.json` holds **70** hand-written complaints (10 per department) with **~72% unique tokens not present** in the ORR vocabulary.

## Run

```powershell
cd offline-routing-research
.\.venv\Scripts\activate
python scripts/evaluate_paraphrase_oov.py
```

Output: `artifacts/paraphrase_oov_eval.json` plus a printed accuracy table.

## Latest result (same train split as other scripts)

| Split | TF-IDF + LR | Embedding k-NN (MiniLM, k=5) |
|--------|-------------|------------------------------|
| ORR holdout (baseline) | 100% | 100% |
| **Paraphrase OOV v1** | **61.43%** | **68.57%** |

Macro-F1 on paraphrase set: **61.86%** (TF-IDF) vs **68.73%** (k-NN).

**Interpretation:** When wording diverges from the simulated corpus, **embedding k-NN wins**; both models drop sharply vs holdout, which is expected and honest for a project write-up.

Production Humanizr routing remains **Gemini** — this is offline research only.
