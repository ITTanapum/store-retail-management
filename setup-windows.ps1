$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "[1/5] Checking Python..." -ForegroundColor Cyan
py -3.12 --version

Write-Host "[2/5] Creating Python virtual environment..." -ForegroundColor Cyan
if (-not (Test-Path "$Root\.venv")) {
    py -3.12 -m venv "$Root\.venv"
}

Write-Host "[3/5] Installing backend packages..." -ForegroundColor Cyan
& "$Root\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "$Root\.venv\Scripts\python.exe" -m pip install -r "$Root\backend\requirements.txt"

Write-Host "[4/5] Preparing environment files..." -ForegroundColor Cyan
if (-not (Test-Path "$Root\backend\.env")) {
    Copy-Item "$Root\backend\.env.example" "$Root\backend\.env"
    Write-Host "Created backend\.env. Edit its SQL Server connection values before initialization." -ForegroundColor Yellow
}
if (-not (Test-Path "$Root\frontend\.env")) {
    Copy-Item "$Root\frontend\.env.example" "$Root\frontend\.env"
}

Write-Host "[5/5] Installing frontend packages..." -ForegroundColor Cyan
Push-Location "$Root\frontend"
npm install
Pop-Location

Write-Host "Setup completed. Next: create the SQL Server database, edit backend\.env, then run initialize-database.ps1." -ForegroundColor Green
