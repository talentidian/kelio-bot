$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

if (-not (Test-Path ".venv")) {
  Write-Host "creating venv"
  python -m venv .venv
}

& ".venv\Scripts\Activate.ps1"

pip install -r requirements.txt
python -m playwright install chromium

Write-Host ""
Write-Host "running login.py - a Chromium window will open"
python login.py