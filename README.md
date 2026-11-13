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

Short version: **[docs/HOW_TO_RUN.md](docs/HOW_TO_RUN.md)**.

Local ports stay fixed: web **3000**, API **8002**, queue **3030**, Redis **6380**. Docker Compose publishes the API on **8000** — use one mode at a time, and point `NEXT_PUBLIC_API_URL` at the API you actually started.

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

**One command** (from repo root — starts Redis in Docker, then opens three windows for API, queue, and frontend):

```powershell
npm start
```

Same thing: `.\start.ps1` or `.\scripts\start-local.ps1`. **Docker Desktop** must be running first. The API window can take **1–2 minutes** on first boot (ML libs); wait for `Application startup complete`, then open http://localhost:3000.

<details>
<summary>Manual four-terminal setup (optional)</summary>

**Terminal 1 — Redis** (skip if `humanizr-redis` is already running)

```powershell
docker run -d -p 6380:6379 --name humanizr-redis redis:7-alpine
```

**Terminal 2 — API**

```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

**Terminal 3 — Queue**

```powershell
cd queue
npm run dev
```

**Terminal 4 — Frontend**

```powershell
cd frontend
npm run dev
```

</details>

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
- **Wrong API port** — local `npm start` and `backend/start-api.ps1` use **8002**. Docker Compose publishes the API on **8000**. `frontend/.env.local` must match the one you started.
- **Port in use** — stop the process using 8002/3000/3030 or change ports consistently in env files.

**Complaint flow:** citizen submits → **Submitted** → BullMQ job → review/routing → **routed to department** → dept admin assigns officer.

### Docker

```bash
docker compose up -d
# Optional separate AI container:
docker compose --profile ai-split up -d
```

### Demo logins (local dev)

Create accounts and sample complaints (after MongoDB is reachable):

```powershell
cd backend
.\venv\Scripts\activate
python scripts\seed_demo_data.py
```

**Login URL:** http://localhost:3000/login — staff and citizens use the same page; the app sends you to the portal for your role.

**Passwords (seed script only — not for production):**

| Role | Password |
|------|----------|
| System administrator | `Admin@123` |
| Department administrator | `DeptAdmin@123` |
| Field officer | `Officer@123` |
| Citizen (resident) | `Citizen@123` |

**Email convention:** municipal staff → `firstname.lastname@civic.gov.in`; residents → personal email (Gmail, Yahoo, Outlook), not `@civic.gov.in`.

#### Municipal departments (AI routing targets)

| Code | Department |
|------|------------|
| PWD | Public Works Department |
| SAN | Sanitation Department |
| WSD | Water Supply Department |
| ELEC | Electricity Department |
| TNT | Traffic & Transport |
| PAR | Parks & Recreation |

#### System administrators (city-wide)

| Name | Email | Password |
|------|-------|----------|
| Arjun Malhotra | arjun.malhotra@civic.gov.in | Admin@123 |
| Nisha Rao | nisha.rao@civic.gov.in | Admin@123 |

#### Department administrators and field officers (by department)

**SAN — Sanitation**

| Role | Name | Email | Password |
|------|------|-------|----------|
| Dept admin | Meera Iyer | meera.iyer@civic.gov.in | DeptAdmin@123 |
| Dept admin | Vikram Desai | vikram.desai@civic.gov.in | DeptAdmin@123 |
| Officer | Ravi Kumar | ravi.kumar@civic.gov.in | Officer@123 |
| Officer | Lakshmi Nair | lakshmi.nair@civic.gov.in | Officer@123 |

**PWD — Public Works**

| Role | Name | Email | Password |
|------|------|-------|----------|
| Dept admin | Karan Singh | karan.singh@civic.gov.in | DeptAdmin@123 |
| Dept admin | Anita Khurana | anita.khurana@civic.gov.in | DeptAdmin@123 |
| Officer | Imran Sheikh | imran.sheikh@civic.gov.in | Officer@123 |
| Officer | Deepa Joshi | deepa.joshi@civic.gov.in | Officer@123 |

**WSD — Water Supply**

| Role | Name | Email | Password |
|------|------|-------|----------|
| Dept admin | Rohit Banerjee | rohit.banerjee@civic.gov.in | DeptAdmin@123 |
| Dept admin | Manish Gupta | manish.gupta@civic.gov.in | DeptAdmin@123 |
| Officer | Mohit Agarwal | mohit.agarwal@civic.gov.in | Officer@123 |
| Officer | Naveen Reddy | naveen.reddy@civic.gov.in | Officer@123 |

**ELEC — Electricity**

| Role | Name | Email | Password |
|------|------|-------|----------|
| Dept admin | Sunita Pillai | sunita.pillai@civic.gov.in | DeptAdmin@123 |
| Dept admin | Pooja Saxena | pooja.saxena@civic.gov.in | DeptAdmin@123 |
| Officer | Farhan Ali | farhan.ali@civic.gov.in | Officer@123 |
| Officer | Shreya Bhatia | shreya.bhatia@civic.gov.in | Officer@123 |

**TNT — Traffic & Transport**

| Role | Name | Email | Password |
|------|------|-------|----------|
| Dept admin | Aditya Venkatesh | aditya.venkatesh@civic.gov.in | DeptAdmin@123 |
| Dept admin | Kavita Menon | kavita.menon@civic.gov.in | DeptAdmin@123 |
| Officer | Sanjay Rawat | sanjay.rawat@civic.gov.in | Officer@123 |
| Officer | Preeti Gautam | preeti.gautam@civic.gov.in | Officer@123 |

**PAR — Parks & Recreation**

| Role | Name | Email | Password |
|------|------|-------|----------|
| Dept admin | Gaurav Mehta | gaurav.mehta@civic.gov.in | DeptAdmin@123 |
| Dept admin | Leela Rajan | leela.rajan@civic.gov.in | DeptAdmin@123 |
| Officer | Anjali Deshmukh | anjali.deshmukh@civic.gov.in | Officer@123 |
| Officer | Harish Patel | harish.patel@civic.gov.in | Officer@123 |

#### Citizens (residents)

| Name | Email | Password |
|------|-------|----------|
| Priya Sharma | priya.sharma@gmail.com | Citizen@123 |
| Rahul Mehta | rahul.mehta88@yahoo.com | Citizen@123 |
| Amit Verma | amit.verma@outlook.com | Citizen@123 |
| Neha Kapoor | neha.kapoor@gmail.com | Citizen@123 |

New residents can also [sign up](http://localhost:3000/sign-in) with any email; seeded citizens above are for demos and sample complaints.

#### Sample data notes

Seeded complaints span **submitted**, **routed**, **assigned**, **in progress**, **resolved**, and **rejected** (unsupported / not on portal). Notifications for every role use the **header bell** only.

#### Who can create which accounts

| Who | How they get an account |
|-----|-------------------------|
| **Residents** | Self [sign-in](http://localhost:3000/sign-in) or use a seeded citizen above |
| **Officers** | Department admin → **Field team**, or system admin → **Staff** |
| **Department admins & system admins** | System admin → **Staff** only |

Source of truth for adding users: `backend/scripts/seed_demo_data.py` (`DEMO_USERS`).

## Documentation

- [Components & need flow (plain English)](docs/NEED_FLOW.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Database Schema](docs/DATABASE.md)
- [Deploy whole project (Docker / Vercel / Render)](docs/DEPLOY_FULL_STACK.md)
- [Deployment (Azure)](docs/DEPLOYMENT.md)

## License

MIT — Final Year B.Tech Project
