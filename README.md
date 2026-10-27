# Humanizr

**AI Powered Smart Civic Complaint Management and Municipal Decision Support System**

Humanizr helps municipalities manage thousands of civic complaints with AI classification, duplicate detection, priority prediction, area clusters, heatmaps, and an immutable blockchain-style audit trail.

## Architecture

| Layer | Stack | Local port |
|-------|--------|------------|
| Frontend | Next.js 14, TypeScript, Tailwind, shadcn/ui, Leaflet | **3000** |
| API | FastAPI, Motor (MongoDB), JWT + RBAC | **8002** |
| Queue | Node + BullMQ worker (complaint AI jobs) | **3030** |
| Redis | Job store + live notification pub/sub | **6380** |
| Database | MongoDB (users, complaints, notifications) | **27017** |
| AI routing | Gemini in API (`backend/app/ai/`) | — |
| Media | Cloudinary (complaint photos) | — |

**Flow:** Citizen submits → API saves `submitted` → enqueue to Redis/BullMQ → worker calls API `/internal/.../process-ai` → Gemini routes to **PWD, SAN, WSD, ELEC, TNT, or PAR** → dept admin assigns officer → resolved.

Open the interactive diagram in the IDE: **Humanizr System Architecture** canvas (`canvases/humanizr-system-architecture.canvas.tsx`).

```
frontend/   → Citizen, officer, dept admin, super admin portals
backend/    → REST API, AI pipeline, blockchain audit, analytics
queue/      → BullMQ enqueue + worker (requires Redis 6380)
ai/         → Optional split AI service (docker profile `ai-split`)
```

## Features (end-to-end)

- **Citizens:** sign in (new account), log in (returning), forgot password, submit complaints (GPS + Leaflet map, images), track status, notifications, feedback
- **AI:** BullMQ + Redis queue processes new complaints via Gemini (department, category, priority), duplicate detection, image verification
- **Departments:** dashboards, verify AI results, work started → resolved, nearby complaints, **area action plans (clusters)**
- **Super admin:** staff by role (administrators, department heads, field staff, residents), departments, analytics, heatmaps, officer workload
- **Audit:** hash-chained status history (`/api/v1/audit/...`)

## How to start (local development)

Use **four terminals** (or background processes). The frontend and queue are configured for the API on **port 8002** — keep that port unless you change env files everywhere.

### Prerequisites

- **Node.js** 18+ and **Python** 3.11+
- **MongoDB** connection string in `backend/.env` (`MONGODB_URI`, `JWT_SECRET_KEY`, Cloudinary, `GEMINI_API_KEY` for complaint routing)
- **Docker Desktop** (recommended) for Redis on host port **6380**

### One-time setup

```powershell
# From repo root — copy env templates if you have not already
copy .env.example .env

cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
# Edit backend\.env (MongoDB, JWT, Cloudinary, GEMINI_API_KEY, CORS for 3000/3001/3002)

cd ..\frontend
npm install
# Create frontend\.env.local:
#   NEXT_PUBLIC_API_URL=http://localhost:8002/api/v1

cd ..\queue
npm install
# Copy queue\.env.example → queue\.env and set:
#   BACKEND_URL=http://127.0.0.1:8002
#   REDIS_URL=redis://127.0.0.1:6380
```

Seed **departments, users (all roles), and sample complaints** (after MongoDB is reachable):

```powershell
cd backend
.\venv\Scripts\activate
python scripts\seed_demo_data.py
# Optional: smoke-test login + complaint lists (API must be running on 8002):
python scripts\seed_demo_data.py --verify
```

Legacy minimal users only: `python scripts\seed_roles.py`

### Every time you run the app

**Terminal 1 — Redis** (skip if `humanizr-redis` is already running)

```powershell
docker run -d -p 6380:6379 --name humanizr-redis redis:7-alpine
```

**Terminal 2 — API**

```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

First startup can take 1–2 minutes while Python loads ML dependencies; wait until you see `Application startup complete`.

**Terminal 3 — Queue worker** (processes new complaints after submit)

```powershell
cd queue
npm run dev
```

You should see: `Queue service listening on http://127.0.0.1:3030`.

**Terminal 4 — Frontend**

```powershell
cd frontend
npm run dev
```

### URLs

| Service | URL |
|---------|-----|
| Web app | http://localhost:3000 |
| API | http://127.0.0.1:8002 |
| OpenAPI | http://127.0.0.1:8002/docs |
| Queue HTTP | http://127.0.0.1:3030 |

### Quick health check

```powershell
Invoke-RestMethod http://127.0.0.1:8002/health
```

Expect `status: healthy` and `db: connected`.

### Troubleshooting

- **Frontend “Cannot reach API”** — API must be on **8002** and `frontend/.env.local` must match; restart `npm run dev` after env changes.
- **Complaints stuck on Submitted** — start Redis (6380) and the **queue** worker; `queue/.env` `BACKEND_URL` must be `http://127.0.0.1:8002`.
- **Old API on 8000** — stop extra uvicorn processes; only run the **8002** instance above.
- **Port in use** — stop the process using 8002/3000/3030 or change ports consistently in env files.

**Complaint flow:** citizen submits → **Submitted** → BullMQ job → review/routing → **routed to department** → dept admin assigns officer.

### Docker

```bash
docker compose up -d
# Optional separate AI container:
docker compose --profile ai-split up -d
```

### Demo logins (local dev)

Run `python scripts/seed_demo_data.py` — it prints the full account list grouped by role.

**Convention:** municipal staff use **firstname.lastname@civic.gov.in**; **residents use personal email** (Gmail, Yahoo, Outlook), not `@civic.gov.in`.

| Role | Example people (password) |
|------|---------------------------|
| **System admin** | Arjun Malhotra, Nisha Rao (`Admin@123`) |
| **Dept admin** | Meera Iyer (SAN), Karan Singh (PWD), Rohit Banerjee (WSD), … (`DeptAdmin@123`) |
| **Officer** | Ravi Kumar (SAN), Imran Sheikh (PWD), Farhan Ali (ELEC), … (`Officer@123`) |
| **Citizen** | Priya Sharma, Rahul Mehta, Sai Bhavani Kokanti, … (`Citizen@123`) |

Examples to log in quickly:

- Citizen: `priya.sharma@gmail.com` / `Citizen@123`
- SAN dept admin: `meera.iyer@civic.gov.in` / `DeptAdmin@123`
- SAN officer: `ravi.kumar@civic.gov.in` / `Officer@123`
- System admin: `arjun.malhotra@civic.gov.in` / `Admin@123`

Sample complaints cover **submitted**, **routed**, **assigned**, **in progress**, **resolved**, and **not on portal** (rejected) states.

Notifications for every role use the **header bell** only.

**Accounts**

| Who | How they get an account |
|-----|-------------------------|
| **Residents (citizens)** | [Sign in](http://localhost:3000/sign-in) once to create an account, then [log in](http://localhost:3000/login) on later visits |
| **Officers** | Department admin → **Field team**, or system admin → **Staff** |
| **Department admins & system admin** | System admin → **Staff** only |

Staff and residents share one **log in** page; after authentication you are sent to the portal for your role.

## Documentation

- [Components & need flow (plain English)](docs/NEED_FLOW.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Database Schema](docs/DATABASE.md)
- [Deploy whole project (Docker / Vercel / Render)](docs/DEPLOY_FULL_STACK.md)
- [Deployment (Azure)](docs/DEPLOYMENT.md)

## License

MIT — Final Year B.Tech Project
