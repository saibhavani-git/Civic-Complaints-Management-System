# Humanizr — components and need flow

This document explains **what the system is made of** and **how work moves through it**, in plain English. Use it for demos, reports, and viva prep.

For deeper technical trade-offs, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## What Humanizr does (one sentence)

Citizens report civic problems (with location and photos); **AI routes** each report to the right **municipal department**, staff **assign and fix** it, and everyone can **track status** with notifications and an audit trail.

---

## All components (what runs where)

### Things you run on your machine (local dev)

| Component | Folder / service | Port | What it does |
|-----------|------------------|------|----------------|
| **Web app** | `frontend/` | **3000** | Screens for citizens, officers, department admins, and system admins. Maps, forms, dashboards, notification bell. |
| **API (backend)** | `backend/` | **8002** | Login, save complaints, permissions, analytics, audit, and the **AI pipeline** when the worker calls in. |
| **Queue service** | `queue/` | **3030** | Accepts “process this complaint” jobs and runs a **worker** that calls the API in the background. |
| **Redis** | Docker (`humanizr-redis`) | **6380** | Stores **BullMQ jobs** and sends **live update events** to the web app (SSE). |
| **MongoDB** | Your Atlas URI or local | **27017** | **Database** — users, complaints, departments, notifications, audit history. |

### External services (cloud accounts)

| Service | Used for |
|---------|----------|
| **Gemini (Google AI)** | Reads complaint text (and images when provided) and picks **department**, **category**, **priority**, or **not on portal**. |
| **Cloudinary** | Stores **complaint photos** and gives URLs the app can show. |
| **MongoDB Atlas** | Same as MongoDB above; typical choice for hosted database. |

### Code folders that are not separate servers

| Folder | Role |
|--------|------|
| `backend/app/api/v1/` | Public REST APIs (complaints, auth, admin, …). |
| `backend/app/api/v1/internal.py` | **Worker-only** route to run AI — not for browsers. Protected by an internal API key. |
| `backend/app/services/` | Business logic: create complaint, change status, notifications, queue recovery. |
| `backend/app/ai/` | Gemini routing, duplicate detection (embeddings), pipeline that ties steps together. |
| `ai/` | Optional separate AI container (`docker compose --profile ai-split`) — not required for normal demo. |
| `offline-routing-research/` | **Research only** — TF-IDF, XGBoost, embedding k-NN on a local dataset. **Not connected** to the live app unless you integrate it later. |
| `docs/` | Architecture, API, deployment guides. |

---

## People and roles (four portals)

| Who | Logs in as | Main job in the app |
|-----|------------|---------------------|
| **Citizen** | Personal email (e.g. Gmail) | Submit complaints, track **own** cases, give feedback. |
| **Field officer** | `@civic.gov.in` staff account | Work on **assigned** complaints, update progress, see reporter contact details. |
| **Department admin** | `@civic.gov.in` | See **department queue**, check AI routing, **assign** complaints to officers. |
| **System admin** | `@civic.gov.in` | Manage **all staff**, departments, city-wide analytics and heatmaps. |

**Departments the AI can route to (six codes):**

| Code | Typical issues |
|------|------------------|
| **PWD** | Roads, footpaths, bridges |
| **SAN** | Garbage, sanitation, waste |
| **WSD** | Water supply, leaks, pressure |
| **ELEC** | Street lights, wires, power |
| **TNT** | Traffic signals, parking, crossings |
| **PAR** | Parks, playgrounds, greenery |

If the issue is **outside** these (e.g. police, passport, airline refund), the system marks it **not supported** and the complaint is **rejected** with a clear message to the citizen.

---

## What must be running for a full demo

Minimum for “submit → AI route → assign → resolve”:

1. **MongoDB** reachable (`MONGODB_URI` in `backend/.env`).
2. **Redis** on port **6380**.
3. **Backend** on port **8002**.
4. **Queue** on port **3030** (`queue/.env`: `BACKEND_URL`, `REDIS_URL`, internal key matches backend).
5. **Frontend** on port **3000** (`NEXT_PUBLIC_API_URL=http://localhost:8002/api/v1`).
6. Valid **`GEMINI_API_KEY`** (and Cloudinary if you upload images).

Quick check: open `http://127.0.0.1:8002/health` — should say database connected.

---

## Main need flow: new complaint (step by step)

This is the **most important flow** in the project.

```
Citizen fills form → API saves complaint → Queue picks job → AI runs → Department gets case → Admin assigns officer → Officer resolves
```

### Step 1 — Citizen submits

1. Citizen opens the web app, logs in, and creates a complaint: **title**, **description**, **location** (map/GPS), optional **photos**.
2. Browser sends data to the **API** with a JWT token.
3. API uploads images to **Cloudinary** (if any).
4. API writes a new document in **MongoDB** with status **`submitted`**.
5. API responds quickly so the citizen is not waiting on AI.

### Step 2 — Background job starts

1. API asks the **queue service** to enqueue a job (`POST` to port **3030**).
2. Queue stores the job in **Redis** (BullMQ).
3. The **worker** (same Node process as the queue) takes the job.
4. Worker calls the API **internal** endpoint: “process AI for this complaint id” (with **internal API key**, not the citizen’s JWT).

### Step 3 — AI processing

1. Complaint status moves to **`ai_processing`**.
2. **Gemini** reads text (+ images when present) and returns:
   - department (or unsupported),
   - category,
   - priority (low / medium / high / critical),
   - short summary for officials.
3. **Duplicate detection** runs: embed the text, compare to nearby recent complaints in MongoDB (similar wording + location).
4. Results are saved in **`ai_metadata`** on the complaint.

### Step 4 — Routed or rejected

**If supported department:**

- Status becomes **`routed_to_department`**.
- Complaint appears in that **department admin’s queue**.

**If not supported:**

- Status becomes **`rejected`**.
- Citizen sees a **friendly message** (no raw “Gemini” or “queue” jargon in their timeline).

### Step 5 — Department admin assigns

1. Department admin opens the department queue.
2. They review AI suggestion (department, priority).
3. They pick a **field officer** (often considering service area).
4. Status becomes **`assigned`**; officer gets the case.

### Step 6 — Officer works and closes

1. Officer updates status, for example:
   - **`work_started`** or **`in_progress`** while fixing,
   - **`resolved`** when done.
2. Each change is recorded in **status history** (audit chain).
3. Citizen can track progress on their complaint page.

### Step 7 — Notifications and live UI

1. When important events happen, the API creates **notifications** in MongoDB.
2. API also publishes an event on **Redis**.
3. The web app listens via **SSE** (server-sent events) and refreshes the **bell icon** and lists without manual reload.

---

## Complaint status flow (simple diagram)

Happy path:

```
submitted → ai_processing → routed_to_department → assigned → work_started / in_progress → resolved
```

Optional later:

```
resolved → feedback_received   (citizen rates the fix)
```

Not on portal:

```
submitted → ai_processing → rejected
```

Some older records may still show legacy values like `pending`, `closed`, or `ai_processed`; new flow uses the names above.

---

## Other important flows

### Login and security

1. User enters email + password on the web app.
2. API checks password (bcrypt) and returns **access JWT** (+ refresh token stored server-side).
3. Every API call sends `Authorization: Bearer <token>`.
4. API checks **role** (`citizen`, `officer`, `dept_admin`, `admin`) before allowing an action.

### Citizen sign-up

1. New resident uses **sign-in / register** (personal email).
2. Account is created as **citizen** only.
3. Staff accounts are created by **system admin** or **department admin** (not self-service `@civic.gov.in` signup in normal demo).

### Analytics and heatmaps (admins)

1. Admin opens analytics pages in the frontend.
2. Frontend calls API aggregation endpoints.
3. Data comes from **MongoDB** (complaint locations, counts by status/priority/department).
4. **Leaflet** maps show clusters and heatmaps.

### Audit trail

1. Status changes append to **status_history** with hash chaining.
2. Audit API lets authorized roles prove the timeline was not tampered with.

### If queue or Redis is down

- New complaints may stay on **`submitted`** until the worker runs again.
- API can **retry** enqueue and has **recovery on startup** to re-enqueue stale complaints.
- Script: `backend/scripts/requeue_submitted_complaints.py`.

---

## How components talk (one picture)

```
┌──────────────┐         REST + JWT          ┌──────────────┐
│   Browser    │ ◄──────────────────────► │   FastAPI    │
│  (Next.js)   │         SSE (live)        │   :8002      │
└──────────────┘                           └──────┬───────┘
                                                  │
         ┌────────────────────────────────────────┼────────────────────────┐
         │                                        │                        │
         ▼                                        ▼                        ▼
┌──────────────┐                         ┌──────────────┐         ┌──────────────┐
│ Queue :3030  │ ──worker calls API──►  │   MongoDB    │         │  Cloudinary  │
│ + BullMQ     │                         │  (all data)  │         │   (photos)   │
└──────┬───────┘                         └──────────────┘         └──────────────┘
       │
       ▼
┌──────────────┐                         ┌──────────────┐
│ Redis :6380  │                         │ Gemini API   │
│ jobs + pub/sub│                        │ (AI routing) │
└──────────────┘                         └──────────────┘
```

**Remember:** The “department queue” in the UI is **complaints in MongoDB** waiting for staff — it is **not** a second Redis queue.

---

## AI pipeline (what happens inside one job)

Order of work when the worker triggers `process-ai`:

1. **Gemini** — department, category, priority, unsupported or not.
2. **Category helper** — backup / consistency from keywords if needed.
3. **Duplicate check** — embedding similarity + geo radius; may link duplicate groups.
4. **Image verification** — heuristic check that photos match the story (full vision routing is via Gemini when images are sent there).
5. **Save** — update complaint, write `ai_results`, notify citizen and staff.

**Priority today** comes mainly from **Gemini**. The codebase also has **duplicate-based priority boost** logic that can be wired more strongly if you move to a hybrid design (embedding routing + image-only LLM for severity).

---

## Offline ML research (separate from production)

Folder: **`offline-routing-research/`**

- Purpose: compare **keyword**, **TF-IDF + logistic regression**, **XGBoost**, **embedding k-NN** on a local dataset.
- Does **not** replace Gemini in the live app unless you integrate it into `backend/app/ai/pipeline.py`.
- Useful for thesis: show why **embedding k-NN** handles **new wording** better than pure TF-IDF on the paraphrase test set.

Production routing in the deployed app: **Gemini**.

---

## Deployment shape (when not on localhost)

Same logical flow; different hosts:

| Piece | Typical free/cheap host |
|-------|-------------------------|
| Frontend | Vercel |
| API | Render, Fly.io, or a small VM |
| Queue worker | Same provider as API (second service) |
| Redis | Upstash |
| MongoDB | Atlas M0 |
| Images | Cloudinary |
| AI | Gemini API key on the API |

See [DEPLOYMENT.md](DEPLOYMENT.md) for Azure and Docker notes.

---

## Glossary (short)

| Term | Meaning |
|------|---------|
| **JWT** | Login token the browser sends to the API. |
| **BullMQ** | Job queue library; jobs live in Redis. |
| **SSE** | Live stream from API to browser for notifications. |
| **Enqueue** | “Add this complaint to the AI job queue.” |
| **Internal API key** | Secret shared only between queue worker and API. |
| **ai_metadata** | JSON on the complaint with AI routing, confidence, duplicates, etc. |
| **UNSUPPORTED** | AI decision: this portal does not handle that issue. |

---

## Related docs

- [ARCHITECTURE.md](ARCHITECTURE.md) — topology, trade-offs, failure modes  
- [API.md](API.md) — endpoints  
- [DATABASE.md](DATABASE.md) — collections and fields  
- [DEPLOYMENT.md](DEPLOYMENT.md) — production and Docker  
- [README.md](../README.md) — how to start locally and demo logins  
