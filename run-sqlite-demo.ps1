$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Env:DB_ENGINE = "sqlite"

if (-not (Test-Path "$Root\.venv\Scripts\python.exe")) {
    py -3.12 -m venv "$Root\.venv"
    & "$Root\.venv\Scripts\python.exe" -m pip install -r "$Root\backend\requirements.txt"
}
if (-not (Test-Path "$Root\frontend\node_modules")) {
    Push-Location "$Root\frontend"; npm install; Pop-Location
}

Push-Location "$Root\backend"
& "$Root\.venv\Scripts\python.exe" manage.py migrate
& "$Root\.venv\Scripts\python.exe" manage.py seed_demo
Pop-Location

& "$Root\start-dev.ps1"
