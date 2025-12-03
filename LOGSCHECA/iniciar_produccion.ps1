# Script de inicio en MODO PRODUCCIÓN para LOGSCHECA
# BioStar Debug Monitor

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "                    INICIANDO LOGSCHECA - MODO PRODUCCIÓN" -ForegroundColor Cyan
Write-Host "                          BioStar Debug Monitor" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que existe el entorno virtual
if (-not (Test-Path "venv")) {
    Write-Host "ERROR: Entorno virtual no encontrado" -ForegroundColor Red
    Write-Host "Ejecuta primero: .\instalar.ps1" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar que existe el archivo .env
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: Archivo .env no encontrado" -ForegroundColor Red
    Write-Host "Copia .env.example a .env y configura tus credenciales" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Activar entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1
Write-Host "[OK] Entorno virtual activado" -ForegroundColor Green
Write-Host ""

# Verificar puerto 5000
Write-Host "Verificando puerto 5000..." -ForegroundColor Cyan
$portInUse = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue

if ($portInUse) {
    Write-Host "[!] El puerto 5000 ya está en uso" -ForegroundColor Yellow
    Write-Host "Procesos usando el puerto 5000:" -ForegroundColor Yellow
    Get-Process -Id $portInUse.OwningProcess | Format-Table -Property Id, ProcessName, StartTime
    Write-Host ""
    $response = Read-Host "¿Deseas continuar de todas formas? (S/N)"
    
    if ($response -ne "S" -and $response -ne "s") {
        Write-Host "Inicio cancelado" -ForegroundColor Yellow
        exit 0
    }
} else {
    Write-Host "[OK] Puerto 5000 disponible" -ForegroundColor Green
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "                        MODO PRODUCCIÓN ACTIVADO" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuración:" -ForegroundColor White
Write-Host "  - Servidor: Waitress (WSGI Production Server)" -ForegroundColor White
Write-Host "  - Host: 0.0.0.0 (accesible desde red)" -ForegroundColor White
Write-Host "  - Puerto: 5000" -ForegroundColor White
Write-Host "  - Debug: DESACTIVADO" -ForegroundColor White
Write-Host "  - Seguridad: NIVEL GOBIERNO" -ForegroundColor White
Write-Host "  - Rate Limiting: ACTIVADO" -ForegroundColor White
Write-Host "  - CSRF Protection: ACTIVADO" -ForegroundColor White
Write-Host "  - Session Security: ACTIVADO" -ForegroundColor White
Write-Host ""
Write-Host "URLs de acceso:" -ForegroundColor Cyan
Write-Host "  - Local: http://localhost:5000" -ForegroundColor Yellow
Write-Host "  - Red: http://10.0.0.10:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "[!] Presiona Ctrl+C para detener el servidor" -ForegroundColor Yellow
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Iniciar el servidor con Waitress (producción)
py run_production.py
