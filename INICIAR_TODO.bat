@echo off
echo ==========================================
echo   BioStar Monitor - Iniciando Todo
echo ==========================================
echo.

cd /d "%~dp0"

echo [1/2] Iniciando aplicacion...
start "BioStar Monitor" powershell -ExecutionPolicy Bypass -File "%~dp0iniciar_produccion.ps1"
timeout /t 3 /nobreak >nul

echo [2/2] Iniciando auto-deploy...
start "Auto-Deploy" powershell -ExecutionPolicy Bypass -File "%~dp0iniciar_auto_deploy.ps1"

echo.
echo ==========================================
echo   TODO INICIADO
echo ==========================================
echo.
echo Aplicacion: http://localhost:5000
echo Auto-Deploy: Monitoreando GitHub cada 60 segundos
echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul
