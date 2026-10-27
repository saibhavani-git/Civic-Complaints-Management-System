# System Architecture

**Humanizr** — civic complaint management with async Gemini routing, four roles, six departments, and a modular monolith layout (not microservices by default).

Print figure: [`architecture-bw.svg`](architecture-bw.svg)

Interactive canvas in the IDE: `canvases/humanizr-architecture-and-tradeoffs.canvas.tsx`

## 1. System context

| Actor | Interface | Backend access |
|-------|-----------|------------------|
| Citizen | Next.js `:3000` — submit, track, feedback | JWT `citizen` — own complaints only |
| Field officer | Officer portal — assigned cases | JWT `officer` — assigned complaints + reporter contact |
| Department admin | Admin portal — department queue, assign | JWT `dept_admin` — dept-scoped complaints |
| System admin | Admin — city-wide staff, analytics | JWT `admin` — all complaints and users |

**Departments (AI routing targets):** PWD, SAN, WSD, ELEC, TNT, PAR.

## 2. Runtime topology (local)

```
┌─────────────┐     HTTPS/JWT      ┌──────────────┐
│  Next.js    │ ◄────────────────► │   FastAPI    │ :8002
│  :3000      │     SSE events     │   backend    │
└─────────────┘                    └──────┬───────┘
                                        │
                    enqueue POST        │ Motor
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
            ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
            │ Queue Node   │    │   MongoDB    │    │  Cloudinary  │
            │ :3030        │    │   :27017     │    │  (images)    │
            │ BullMQ worker│    │ source of    │    └──────────────┘
            └──────┬───────┘    │ truth        │
                   │            └──────────────┘
                   │ worker calls
                   │ POST /internal/.../process-ai
                   ▼
            ┌──────────────┐         ┌──────────────┐
            │    Redis     │         │ Gemini API   │
            │    :6380     │         │ (routing)    │
            │ jobs + pub/sub│         └──────────────┘
            └──────────────┘
```

| Component | Port | Responsibility | If down |
|-----------|------|----------------|---------|
| Next.js frontend | 3000 | UI, React Query, SSE client | No UI |
| FastAPI backend | 8002 | Auth, CRUD, AI pipeline entry, notifications | Total API outage |
| Queue service | 3030 | HTTP enqueue + BullMQ worker | New complaints may stay `submitted`* |
| Redis | 6380 | BullMQ job store; pub/sub for live UI | Jobs + live bell broken* |
| MongoDB | 27017 | Users, complaints, notifications, audit | Total outage |
| Gemini | HTTPS | Department + priority routing | Retry / fallback paths |
| Cloudinary | HTTPS | Complaint photos (optional) | Submit still works without images |

\*The API retries enqueue, can run in-process routing if enqueue fails, and startup recovery re-enqueues stale `submitted` / `ai_processing` rows.

### Not two complaint queues

- **One BullMQ queue** in Redis (`complaint-ai` jobs).
- **Port 3030** is a single Node process: Express enqueue endpoint + worker (not a second queue product).
- The UI **“department queue”** is MongoDB complaints with status `routed_to_department` — not another Redis queue.
- Redis **pub/sub** pushes SSE events; it is not a job queue.

## 3. End-to-end complaint flow

1. **Submit** — Browser → API; images → Cloudinary; MongoDB status **`submitted`**.
2. **Enqueue** — API → `POST :3030/enqueue`; Redis job id typically `complaint-{mongoId}`.
3. **AI routing** — Worker → `POST /internal/.../process-ai` (shared `INTERNAL_API_KEY`); Gemini assigns department/priority; duplicate checks; status → **`routed_to_department`** or **`rejected`** (unsupported).
4. **Assign** — Dept admin picks officer; status **`assigned`** + `assigned_officer_id`.
5. **Resolve** — Officer updates **`work_started`** / **`in_progress`** → **`resolved`**.
6. **Notify** — Notifications collection + Redis pub/sub → SSE refreshes bell and lists.

Citizen-facing timeline notes are **sanitized** (no Gemini/BullMQ/internal queue wording).

## 4. Logical layers (codebase)

### Presentation — `frontend/`

- Next.js 14 App Router with route groups: citizen, officer, admin.
- React Query for server state; shadcn/ui + Tailwind; Leaflet for maps and heatmaps.
- Role-specific complaint filters (`complaintFilters.ts`).
- `useRealtimeSync` — SSE `/api/v1/events/stream`.

### Application — `backend/app/`

- `api/v1` — REST routers; RBAC via JWT dependencies.
- `internal` — worker-only `process-ai` (not for browsers).
- `services` — complaints, notifications, analytics, auth.
- `ai` — Gemini router, pipeline, duplicate detection, `departments_config` (6 codes).
- `integrations/queue_client.py` — enqueue with retries + fallback.
- `services/complaint_queue_recovery.py` — stale job recovery on startup.

### Async worker — `queue/`

- Single process: enqueue HTTP + BullMQ worker (concurrency ~2).
- Calls back into FastAPI with `X-Internal-Key` so Gemini work is off the citizen submit request thread.

### Optional split — `ai/`

- Docker profile `ai-split` if you want AI isolated from the main API later.

### Data

- **MongoDB** — complaints (GeoJSON), users, departments, notifications, hash-chained audit.
- **Redis** — BullMQ + ephemeral pub/sub (not complaint source of truth).

## 5. Authentication flow

```
Client → POST /auth/login → bcrypt verify
       → access JWT (~30m) + refresh JWT (stored server-side)
       → Authorization: Bearer <access> on API calls
       → RBAC: citizen | officer | dept_admin | admin
```

## 6. Role-based access (summary)

| Resource | Citizen | Officer | Dept admin | Admin |
|----------|---------|---------|------------|-------|
| Submit complaint | ✅ | ❌ | ❌ | ❌ |
| Own complaints | ✅ | ❌ | ❌ | ✅ (all) |
| Assigned / dept complaints | ❌ | ✅ | ✅ (dept) | ✅ |
| Update status (assigned) | ❌ | ✅ | ✅ | ✅ |
| Assign officer | ❌ | ❌ | ✅ | ✅ |
| Manage users / departments | ❌ | ❌ | limited | ✅ |
| Analytics / heatmaps | ❌ | limited | dept | ✅ |
| See reporter PII on complaint | ❌ | ✅ | ✅ | ✅ |
| See assigned officer on own complaint | ✅ | — | — | — |

## 7. Security boundaries

| Boundary | Mechanism | Trade-off |
|----------|-----------|-----------|
| Browser ↔ API | JWT + RBAC | Stateless scaling; stolen token window |
| Queue ↔ API | `INTERNAL_API_KEY` | Simple; must never expose to browser |
| Citizen vs staff fields | Reporter fields staff-only | Privacy vs officer outreach |
| AI metadata in UI | Sanitized timeline for citizens | Less internal transparency; cleaner UX |

## 8. Architecture trade-offs

### Async BullMQ vs synchronous AI on submit

**Chosen:** Async queue (+ mitigations).

| Pros | Cons |
|------|------|
| Fast HTTP response for citizens | API + queue + Redis + worker must all be healthy |
| Retries/backoff on Gemini failures | Debugging spans processes |
| Worker concurrency caps API load | Risk of stuck `submitted` if Redis/queue down |

**Mitigations:** enqueue retries, in-process fallback if enqueue fails, startup stale recovery, `queue/npm run inspect`, `requeue_submitted_complaints.py`.

### Modular monolith vs AI microservice

**Chosen:** Monolith with optional `ai/` split.

| Pros | Cons |
|------|------|
| One deploy for demo/thesis | Heavy Python imports on API boot |
| Shared models and DB access | AI stress shares process with HTTP (partially offset by queue calling internal route) |

### MongoDB vs SQL

**Chosen:** MongoDB.

| Pros | Cons |
|------|------|
| Flexible complaint + `ai_metadata` documents | Weaker ad-hoc joins |
| GeoJSON for nearby duplicates/clusters | Reporting via aggregation pipelines |

### Gemini vs pure keyword/embedding classifier

**Chosen:** Gemini primary router to six fixed departments.

| Pros | Cons |
|------|------|
| Handles messy citizen language | Latency, cost, API keys |
| Explicit unsupported/reject path | Non-deterministic; must sanitize UI copy |

### Manual officer assign vs auto-assign on route

**Chosen:** Dept admin assigns from department queue.

| Pros | Cons |
|------|------|
| Matches real municipal workflow | Extra step; cases wait in `routed_to_department` |
| Respects field area and workload UI | Not fully automated |

### Redis for BullMQ + SSE pub/sub

**Chosen:** Same Redis instance in dev.

| Pros | Cons |
|------|------|
| One dependency to run locally | Shared failure domain |
| Low ops for student/demo | Memory pressure from jobs can affect realtime |

### Next.js route groups vs single responsive app

| Pros | Cons |
|------|------|
| Clear role-based URLs and nav | Duplicated shell/layout code |
| Different filters per portal | Role redirect when wrong path |

### Cloudinary vs local/S3

| Pros | Cons |
|------|------|
| CDN URLs, no long-lived blobs in API | Third-party account; uploads must fail soft |

## 9. Failure modes

| Failure | Symptom | Mitigation |
|---------|---------|------------|
| Redis down | `submitted` stuck; SSE quiet | Start Redis on 6380; requeue script; API fallback |
| Queue down | Enqueue errors | Retries; in-process background routing |
| Gemini error | Retries; may revert status | Worker attempts; sanitized history notes |
| Wrong `BACKEND_URL` / key in `queue/.env` | Worker 401 | Align port 8002 and `INTERNAL_API_KEY` |
| Two queue dev processes | Port 3030 conflict | Single `npm run dev` in `queue/` |

## 10. Evolution (beyond demo)

| Direction | When | Cost |
|-----------|------|------|
| Managed Redis + dedicated queue workers | First production pilot | Ops $ |
| Horizontal FastAPI behind LB | High citizen concurrency | Already JWT-stateless |
| Separate AI worker pool | Gemini rate limits | Split enqueue API from workers |
| Analytics warehouse | Heavy reporting | Export aggregations to BI |
| WebSocket gateway vs SSE+Redis | Very chatty realtime | More infra |

## 11. Operational scripts

- `backend/scripts/seed_demo_data.py` — roles, departments, sample complaints.
- `backend/scripts/check_pipeline_health.py` — API, queue, Redis sanity.
- `backend/scripts/requeue_submitted_complaints.py` — recover stuck submits.
- `queue/npm run inspect` — BullMQ job inspection.

## 12. Security checklist (implementation)

- JWT access + refresh rotation; bcrypt passwords.
- Pydantic validation; CORS to frontend origins.
- Upload type/size checks; internal routes key-guarded.
- Optional: field-level encryption for PII in MongoDB.
