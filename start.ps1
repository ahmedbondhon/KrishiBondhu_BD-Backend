# ============================================================
# KrishiBondhu Bangladesh - Start All Services
# ============================================================
# Run this script from the project root:
#   .\start.ps1
#
# Requirements:
#   - Python installed
#   - pip install done: pip install -r backend\requirements.txt
#   - backend\.env configured with your Supabase credentials
# ============================================================

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "  =======================================" -ForegroundColor Green
Write-Host "  KrishiBondhu Bangladesh - Starting Up"  -ForegroundColor Green
Write-Host "  =======================================" -ForegroundColor Green
Write-Host ""

# --- Check .env exists ---
$envFile = Join-Path $root "backend\.env"
if (-not (Test-Path $envFile)) {
    Write-Host "  [!] backend\.env not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item (Join-Path $root "backend\.env.example") $envFile
    Write-Host "  [!] Edit backend\.env with your Supabase credentials first." -ForegroundColor Yellow
    Write-Host ""
}

# --- Start Backend (port 8000) ---
$backendDir = Join-Path $root "backend"
Write-Host "  [1] Starting Backend API  -> http://localhost:8000" -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Write-Host 'Backend starting...' -ForegroundColor Green; Set-Location '$backendDir'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
) -WindowStyle Normal

Start-Sleep -Seconds 2

# --- Start AI Service (port 8001) ---
$aiDir = Join-Path $root "ai-service"
Write-Host "  [2] Starting AI Service   -> http://localhost:8001" -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Write-Host 'AI Service starting...' -ForegroundColor Green; Set-Location '$aiDir'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
) -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "  =======================================" -ForegroundColor Green
Write-Host "  [OK] Both services started!"             -ForegroundColor Green
Write-Host ""
Write-Host "  API Docs    -> http://localhost:8000/api/v1/docs" -ForegroundColor White
Write-Host "  AI Docs     -> http://localhost:8001/internal/docs" -ForegroundColor White
Write-Host "  Health      -> http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "  To stop: close the two terminal windows that opened." -ForegroundColor Gray
Write-Host "  =======================================" -ForegroundColor Green
Write-Host ""
