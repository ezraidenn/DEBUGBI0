@echo off
REM ============================================
REM Instalacion y Ejecucion Auto-Deploy Windows
REM ============================================

echo ==========================================
echo   BioStar Monitor - Auto-Deploy Windows
echo ==========================================
echo.

REM Verificar permisos de administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ADVERTENCIA: Se recomienda ejecutar como Administrador
    echo para configurar el firewall correctamente.
    echo.
    timeout /t 3
)

REM Ejecutar instalacion
powershell -ExecutionPolicy Bypass -File "%~dp0INSTALAR_AUTO_DEPLOY_WINDOWS.ps1"

echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
