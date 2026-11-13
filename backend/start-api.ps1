# Run the Humanizr API from the project venv.
# Local port is 8002 (Docker Compose publishes the API on 8000).
$ErrorActionPreference = "Stop"
$Port = 8002
$Root = $PSScriptRoot

Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match 'uvicorn.*app\.main' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Start-Sleep -Seconds 2
Set-Location $Root
& "$Root\venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port $Port --reload
