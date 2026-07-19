$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = "$Root\.venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Virtual environment not found. Run setup-windows.ps1 first."
}

$BackendCommand = "Set-Location '$Root\backend'; & '$Python' manage.py runserver 0.0.0.0:8000"
$FrontendCommand = "Set-Location '$Root\frontend'; npm run dev -- --host 0.0.0.0"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $BackendCommand
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", $FrontendCommand

Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "Django Admin: http://127.0.0.1:8000/admin/" -ForegroundColor Green
