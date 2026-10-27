# Humanizr — start Redis + API + queue + frontend (Windows PowerShell)
# Run from repo root:  .\scripts\start-local.ps1
# First API boot can take 2–3 minutes (ML libs). Open http://localhost:3000 when ready.

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path "$Root\backend\venv\Scripts\python.exe")) {
    Write-Host "Missing backend venv. Run: cd backend; python -m venv venv; pip install -r requirements.txt"
    exit 1
}

Write-Host "1/4 Redis (Docker port 6380)..."
docker info 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Start Docker Desktop first, then run this script again."
    exit 1
}
$existing = docker ps -a --filter name=humanizr-redis --format "{{.Names}}"
if ($existing -eq "humanizr-redis") { docker start humanizr-redis | Out-Null }
else { docker run -d -p 6380:6379 --name humanizr-redis redis:7-alpine | Out-Null }

Write-Host "2/4 API :8002 (new window)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\backend'; .\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002"

Start-Sleep -Seconds 3
Write-Host "3/4 Queue :3030 (new window)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\queue'; npm run dev"

Start-Sleep -Seconds 2
Write-Host "4/4 Frontend :3000 (new window)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\frontend'; npm run dev"

Write-Host ""
Write-Host "Wait ~2 min, then check: http://127.0.0.1:8002/health"
Write-Host "App: http://localhost:3000"
Write-Host "Demo login: priya.sharma@gmail.com / Citizen@123  (after seed_demo_data.py)"
