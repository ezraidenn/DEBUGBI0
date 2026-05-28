# ============================================
# DEBUGBI0 - launcher PowerShell (desarrollo)
# Para produccion usa NSSM/Windows Service con FLASK_ENV=production
# y un reverse proxy (IIS/nginx) delante con TLS.
# ============================================
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path '.env')) {
    Write-Error "Falta .env. Copia .env.example como .env y configura."
    exit 1
}

if (-not (Test-Path 'venv\Scripts\python.exe')) {
    Write-Error "Falta venv. Crea uno con: python -m venv venv; venv\Scripts\pip install -r requirements.txt"
    exit 1
}

& 'venv\Scripts\python.exe' 'run.py'
