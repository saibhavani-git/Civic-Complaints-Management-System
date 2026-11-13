# Humanizr — start Redis + API + queue + frontend (Windows PowerShell)
#
# From repo root (pick one):
#   npm start
#   .\start.ps1
#   .\scripts\start-local.ps1
#
# Opens three PowerShell windows (API, queue, frontend). First API boot can take 1–2 min.

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Start-HumanizrServiceWindow {
    param(
        [string]$Title,
        [string]$WorkingDir,
        [string]$Command
    )
    $wd = $WorkingDir.Replace("'", "''")
    $cmd = $Command.Replace("'", "''")
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "`$Host.UI.RawUI.WindowTitle = '$Title'; Set-Location -LiteralPath '$wd'; $cmd"
    ) | Out-Null
}

if (-not (Test-Path "$Root\backend\venv\Scripts\python.exe")) {
    Write-Host "Missing backend venv. Run once:"
    Write-Host "  cd backend"
    Write-Host "  python -m venv venv"
    Write-Host "  .\venv\Scripts\pip install -r requirements.txt"
    exit 1
}

Write-Host "Humanizr — starting local stack..." -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] Redis (Docker, host port 6380)..."
try {
    docker info *> $null
} catch {
    Write-Host "Docker is not running. Start Docker Desktop, then run this again." -ForegroundColor Red
    exit 1
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not running. Start Docker Desktop, then run this again." -ForegroundColor Red
    exit 1
}

$existing = docker ps -a --filter "name=^humanizr-redis$" --format "{{.Names}}" 2>$null
if ($existing -eq "humanizr-redis") {
    docker start humanizr-redis | Out-Null
} else {
    docker run -d -p 6380:6379 --name humanizr-redis redis:7-alpine | Out-Null
}
Write-Host "      Redis ready." -ForegroundColor Green

Write-Host "[2/4] API http://127.0.0.1:8002 (new window)..."
Start-HumanizrServiceWindow -Title "Humanizr API :8002" -WorkingDir "$Root\backend" -Command ".\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload"

Start-Sleep -Seconds 2
Write-Host "[3/4] Queue http://127.0.0.1:3030 (new window)..."
Start-HumanizrServiceWindow -Title "Humanizr Queue :3030" -WorkingDir "$Root\queue" -Command "npm run dev"

Start-Sleep -Seconds 1
Write-Host "[4/4] Frontend http://localhost:3000 (new window)..."
Start-HumanizrServiceWindow -Title "Humanizr Frontend :3000" -WorkingDir "$Root\frontend" -Command "npm run dev"

Write-Host ""
Write-Host "All processes launched." -ForegroundColor Green
Write-Host "  Web app:  http://localhost:3000"
Write-Host "  API docs: http://127.0.0.1:8002/docs"
Write-Host "  Health:   http://127.0.0.1:8002/health  (wait until status is healthy)"
Write-Host ""
Write-Host "Demo login (after seed): priya.sharma@gmail.com / Citizen@123"
Write-Host "Close the three service windows to stop API, queue, and frontend."
