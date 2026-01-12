@echo off
REM ============================================
REM Instalacion Completa - BioStar Monitor
REM ============================================

echo ==========================================
echo   BioStar Monitor - Instalacion Completa
echo ==========================================
echo.

REM Verificar PowerShell
where powershell >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: PowerShell no encontrado
    pause
    exit /b 1
)

REM Ejecutar script de PowerShell
powershell -ExecutionPolicy Bypass -File "%~dp0ejecutar_instalacion_completa.ps1"

pause
