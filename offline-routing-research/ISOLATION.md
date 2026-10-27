# Isolation from Humanizr / Grievance

This directory is **standalone research**. It is **not** part of the production app.

| Rule | Status |
|------|--------|
| No Python/TS imports from `backend/`, `frontend/`, `queue/` | Enforced — only local `algorithms/` + `scripts/` |
| No API routes, env vars, or Docker wiring | None |
| No replacement for Gemini | Production routing unchanged |
| Optional Mongo export script | Opt-in only; never run by the main app |

If you deploy Humanizr, you **do not** deploy or install this folder unless you choose to for experiments on a laptop.
