# Deploy Humanizr (whole project)

Humanizr needs **five moving parts** in production:

| # | Piece | Purpose |
|---|--------|---------|
| 1 | **Frontend** (Next.js) | Web UI |
| 2 | **Backend** (FastAPI) | API + AI pipeline |
| 3 | **Queue** (Node + BullMQ) | Background Gemini jobs |
| 4 | **Redis** | Jobs + live notifications (SSE) |
| 5 | **MongoDB** | Database (use **Atlas** free M0) |

Plus **Cloudinary** (photos) and **Gemini API key** (routing).

Pick **one path** below.

---

## Path A — One server with Docker (simplest “whole app”)

Best for: **Oracle Cloud Always Free VM**, a college server, or any Linux box with Docker.

### 1. Prepare cloud accounts (free tier)

1. **MongoDB Atlas** — create M0 cluster → connection string → `MONGODB_URI`
2. **Cloudinary** — cloud name + API key/secret
3. **Google AI Studio** — `GEMINI_API_KEY`
4. Atlas → **Network Access** → allow your server public IP (or `0.0.0.0/0` for demo only)

### 2. Configure environment on the server

```bash
git clone <your-repo-url> humanizr
cd humanizr
cp .env.example .env
nano .env   # or your editor
```

**Required in `.env`:**

```env
MONGODB_URI=mongodb+srv://...
JWT_SECRET_KEY=<long-random-string>
GEMINI_API_KEY=...
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...

# Public URL citizens use in the browser (replace YOUR_IP or domain)
NEXT_PUBLIC_API_URL=http://YOUR_IP:8000/api/v1
CORS_ORIGINS=http://YOUR_IP:3000
FRONTEND_URL=http://YOUR_IP:3000

# Same secret on backend + queue (compose overrides Redis/queue URLs internally)
INTERNAL_API_KEY=<another-long-random-string>
REDIS_URL=redis://redis:6379
QUEUE_SERVICE_URL=http://queue:3030
BACKEND_URL=http://YOUR_IP:8000
```

Generate secrets (PowerShell example):

```powershell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

### 3. Start the stack

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

First backend start can take **several minutes** (Python + spaCy). Watch logs:

```bash
docker compose -f docker-compose.prod.yml logs -f backend
```

Wait until `/health` shows `"db": "connected"` and `"queue": "reachable"`.

### 4. Open firewall ports

On the VM security group / firewall, allow inbound **3000** (web) and **8000** (API) if the browser talks directly to them.

### 5. Seed demo data (once)

From your laptop **or** the server (with `MONGODB_URI` pointing at Atlas):

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
# copy same MONGODB_URI into backend/.env
python scripts/seed_demo_data.py
```

### 6. Smoke test

| URL | Expect |
|-----|--------|
| `http://YOUR_IP:8000/health` | `healthy`, db connected, queue reachable |
| `http://YOUR_IP:3000` | Login page |
| Submit a complaint | Moves past **Submitted** within ~1–2 min |

---

## Path B — Split hosting (Vercel + Render + Upstash)

Best for: demo link with **HTTPS** and no VM admin.

### Overview

```
Vercel (frontend) → Render Web Service (API)
                 → Render Web Service (queue worker)
Upstash Redis ← both API and queue
MongoDB Atlas ← API
```

### 1. MongoDB Atlas

Same as Path A — get `MONGODB_URI`, allow Render outbound IPs or `0.0.0.0/0` for demo.

### 2. Upstash Redis

1. Create database at [upstash.com](https://upstash.com)
2. Copy **`REDIS_URL`** (use the TLS `rediss://` URL if offered)

### 3. Render — Backend (Docker)

1. New **Web Service** → connect GitHub repo
2. **Root directory:** leave default (repo root)
3. **Dockerfile path:** `backend/Dockerfile`
4. **Instance:** Free (sleeps when idle — first request slow)
5. **Environment variables:**

| Key | Value |
|-----|--------|
| `MONGODB_URI` | Atlas string |
| `JWT_SECRET_KEY` | random |
| `GEMINI_API_KEY` | … |
| `CLOUDINARY_*` | … |
| `REDIS_URL` | Upstash URL |
| `QUEUE_SERVICE_URL` | `https://<your-queue-service>.onrender.com` |
| `INTERNAL_API_KEY` | random (match queue) |
| `CORS_ORIGINS` | `https://<your-app>.vercel.app` |
| `FRONTEND_URL` | same Vercel URL |
| `BACKEND_URL` | `https://<your-api>.onrender.com` |

Note the public API URL: `https://<your-api>.onrender.com`

### 4. Render — Queue (Docker)

1. Second **Web Service**
2. **Dockerfile path:** `queue/Dockerfile`
3. **Environment:**

| Key | Value |
|-----|--------|
| `REDIS_URL` | same Upstash |
| `BACKEND_URL` | `https://<your-api>.onrender.com` |
| `INTERNAL_API_KEY` | **same as backend** |
| `COMPLAINT_AI_QUEUE_NAME` | `complaint-ai` |

No public port required for users; Render still exposes HTTPS for health checks. Backend must reach this URL for enqueue — use the Render **public** URL.

### 5. Vercel — Frontend

1. Import repo → **Root Directory:** `frontend`
2. Framework: Next.js (auto)
3. **Environment variable:**

```
NEXT_PUBLIC_API_URL=https://<your-api>.onrender.com/api/v1
```

4. Deploy → copy `https://….vercel.app`
5. Update backend **`CORS_ORIGINS`** and **`FRONTEND_URL`** on Render to that Vercel URL → redeploy API.

### 6. Seed and test

Run `seed_demo_data.py` locally against Atlas (same as Path A step 5).

**Free-tier caveats:**

- Render **sleeps** → cold start 30s–2min; complaints may sit **Submitted** until services wake.
- Backend **Docker build** is heavy; first deploy is slow.
- Upstash has **request limits** on free tier.

---

## Path C — Azure (paid / college credits)

See [DEPLOYMENT.md](DEPLOYMENT.md) for App Service + ACR. You still need **managed Redis**, **queue worker**, and **Atlas** — mirror Path B topology on Azure.

---

## Environment checklist (all paths)

| Variable | Where | Notes |
|----------|--------|--------|
| `MONGODB_URI` | Backend | Atlas |
| `JWT_SECRET_KEY` | Backend | Strong random |
| `GEMINI_API_KEY` | Backend | Required for routing |
| `CLOUDINARY_*` | Backend | Images |
| `REDIS_URL` | Backend + Queue | Same Redis |
| `QUEUE_SERVICE_URL` | Backend | Public or internal URL of queue HTTP |
| `BACKEND_URL` | Backend + Queue | Public API URL (queue calls `/internal/...`) |
| `INTERNAL_API_KEY` | Backend + Queue | **Must match** |
| `CORS_ORIGINS` | Backend | Frontend origin(s), comma-separated |
| `FRONTEND_URL` | Backend | Password reset links |
| `NEXT_PUBLIC_API_URL` | Frontend build | `…/api/v1` |

Optional SMTP — password reset emails; without SMTP, reset links log on the server.

---

## After deploy

```bash
# From backend folder with Atlas URI
python scripts/check_pipeline_health.py
python scripts/requeue_submitted_complaints.py   # if jobs stuck after outage
```

**Health:** `GET /health` → prefer `"status": "healthy"` with queue reachable.

**Demo logins:** see root [README.md](../README.md) after seed.

---

## Common failures

| Symptom | Fix |
|---------|-----|
| Complaints stuck **Submitted** | Queue not running, wrong `QUEUE_SERVICE_URL`, or Redis down |
| Worker **401** | `INTERNAL_API_KEY` mismatch between backend and queue |
| Frontend **CORS** error | Add exact Vercel URL to `CORS_ORIGINS`, redeploy API |
| **Degraded** health, queue unreachable | Queue service down or wrong URL from API container |
| AI never finishes | Missing/invalid `GEMINI_API_KEY`; check Render logs |
| SSE bell quiet but data OK | Redis pub/sub URL wrong on API; notifications still in MongoDB |

---

## What we do not deploy

- **`offline-routing-research/`** — local ML experiments only, not part of production routing unless you integrate it later.

---

## Related docs

- [NEED_FLOW.md](NEED_FLOW.md) — components and flows  
- [ARCHITECTURE.md](ARCHITECTURE.md) — topology  
- [DEPLOYMENT.md](DEPLOYMENT.md) — Azure-focused  
