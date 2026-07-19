$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = "$Root\.venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Virtual environment not found. Run setup-windows.ps1 first."
}
if (-not (Test-Path "$Root\backend\.env")) {
    throw "backend\.env not found. Copy backend\.env.example and configure SQL Server first."
}

Push-Location "$Root\backend"
& $Python manage.py check
& $Python manage.py migrate
& $Python manage.py seed_demo
& $Python manage.py check
Pop-Location

Write-Host "Database initialized and demo accounts created." -ForegroundColor Green
