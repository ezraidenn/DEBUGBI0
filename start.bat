@echo off
REM ============================================
REM DEBUGBI0 - launcher Windows (desarrollo)
REM Para produccion usa NSSM/Windows Service apuntando a:
REM   "%~dp0venv\Scripts\python.exe" "%~dp0run.py"
REM con FLASK_ENV=production y un reverse proxy (IIS/nginx) delante.
REM ============================================
setlocal
cd /d "%~dp0"

if not exist ".env" (
    echo [ERROR] Falta .env. Copia .env.example como .env y configura.
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Falta venv. Crea uno con: python -m venv venv ^&^& venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

"venv\Scripts\python.exe" run.py
endlocal
pause
