# How to run Humanizr

Local app on your machine. One command starts Redis, the API, the queue, and the website.

## Ports

Use these together. Do not mix them with Docker’s API port.

| Service | Address |
|---------|---------|
| Website | http://localhost:3000 |
| API | http://127.0.0.1:8002 |
| API docs | http://127.0.0.1:8002/docs |
| Queue | http://127.0.0.1:3030 |
| Redis | `127.0.0.1:6380` (Docker container `humanizr-redis`) |

Docker Compose is a separate way to run the stack. In that mode the API is published on **port 8000**, not 8002. Run either `npm start` or Docker, not both, and set `NEXT_PUBLIC_API_URL` to the API you started.

## What you need

- Node.js 18+
- Python 3.11+
- Docker Desktop (for Redis)
- `backend/.env` with MongoDB, `JWT_SECRET_KEY`, and `GEMINI_API_KEY`

## First time

From the repo root in PowerShell:

```powershell
copy .env.example .env
copy frontend\.env.example frontend\.env.local
copy queue\.env.example queue\.env

cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Edit `backend\.env` with your MongoDB URI and keys. These URLs should stay as follows (they match `npm start`):

```
BACKEND_URL=http://127.0.0.1:8002
PUBLIC_API_URL=http://127.0.0.1:8002
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000
REDIS_URL=redis://127.0.0.1:6380
QUEUE_SERVICE_URL=http://127.0.0.1:3030
```

`frontend\.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8002/api/v1
```

`queue\.env`:

```
REDIS_URL=redis://127.0.0.1:6380
QUEUE_HTTP_PORT=3030
BACKEND_URL=http://127.0.0.1:8002
```

Install the other two apps, then load demo users:

```powershell
cd frontend
npm install

cd ..\queue
npm install

cd ..\backend
.\venv\Scripts\activate
python scripts\seed_demo_data.py
```

## Every time

Start Docker Desktop, then from the repo root:

```powershell
npm start
```

That opens three windows (API, queue, website). The API can take a minute or two the first time. When that window says `Application startup complete`, open http://localhost:3000.

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8002/health
```

You want `status: healthy` and `db: connected`.

Demo logins are in the main [README](../README.md) (system admin `Admin@123`, field officer `Officer@123`, resident `Citizen@123`).

## Stop

Close the three PowerShell windows. The Redis container can stay running.

## If it fails

- **Website cannot reach the API** — the API window must be on port **8002**, and `frontend/.env.local` must say `http://localhost:8002/api/v1`. Restart `npm run dev` after changing that file.
- **Complaints stay on Submitted** — Redis (6380) and the queue window must be running. `queue/.env` `BACKEND_URL` must be `http://127.0.0.1:8002`.
- **Port already in use** — an old API, queue, or website window is still open. Close it. Local ports are 3000, 8002, and 3030. Port 8000 is only for Docker Compose.
