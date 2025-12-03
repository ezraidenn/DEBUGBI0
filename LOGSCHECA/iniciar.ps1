# Script de inicio rápido para LOGSCHECA
# BioStar Debug Monitor

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INICIANDO LOGSCHECA" -ForegroundColor Cyan
Write-Host "BioStar Debug Monitor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
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
Write-Host "✓ Entorno virtual activado" -ForegroundColor Green
Write-Host ""

# Verificar puerto 5000
Write-Host "Verificando puerto 5000..." -ForegroundColor Cyan
$portInUse = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue

if ($portInUse) {
    Write-Host "⚠ El puerto 5000 ya está en uso" -ForegroundColor Yellow
    Write-Host "Procesos usando el puerto 5000:" -ForegroundColor Yellow
    Get-Process -Id $portInUse.OwningProcess | Format-Table -Property Id, ProcessName, StartTime
    Write-Host ""
    $response = Read-Host "¿Deseas continuar de todas formas? (S/N)"
    
    if ($response -ne "S" -and $response -ne "s") {
        Write-Host "Inicio cancelado" -ForegroundColor Yellow
        exit 0
    }
} else {
    Write-Host "✓ Puerto 5000 disponible" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Iniciando servidor..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Iniciar el servidor
python run_webapp.py
