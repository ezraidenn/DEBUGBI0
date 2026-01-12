# ============================================
# Instalacion Auto-Deploy Windows
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BioStar Monitor - Auto-Deploy Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$REPO_PATH = "C:\Users\Administrador\Documents\DebugBi0\DEBUGBI0"

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "$REPO_PATH\.git")) {
    Write-Host "ERROR: No se encuentra el repositorio Git" -ForegroundColor Red
    Write-Host "Ruta esperada: $REPO_PATH" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Repositorio encontrado" -ForegroundColor Green
Write-Host ""

# Paso 1: Verificar Python
Write-Host "Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python instalado: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "Python no encontrado" -ForegroundColor Red
    Write-Host "Instala Python desde: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Paso 2: Verificar dependencias
Write-Host "Verificando dependencias..." -ForegroundColor Yellow
Push-Location $REPO_PATH

if (-not (Test-Path "venv")) {
    Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

Write-Host "Instalando/actualizando dependencias..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

Write-Host "Dependencias instaladas" -ForegroundColor Green
Write-Host ""

# Paso 3: Verificar .env
Write-Host "Verificando configuracion (.env)..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "Archivo .env encontrado" -ForegroundColor Green
}
else {
    Write-Host "⚠ Archivo .env no encontrado" -ForegroundColor Yellow
    Write-Host "Copiando desde .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Archivo .env creado" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANTE: Edita el archivo .env con tus credenciales" -ForegroundColor Red
}

Write-Host ""

# Paso 4: Crear directorio de logs
Write-Host "Creando directorio de logs..." -ForegroundColor Yellow
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}
Write-Host "Directorio de logs creado" -ForegroundColor Green
Write-Host ""

# Paso 5: Configurar firewall
Write-Host "Configurando firewall de Windows..." -ForegroundColor Yellow
$ruleName = "BioStar Monitor - Puerto 5000"
$existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue

if (-not $existingRule) {
    try {
        New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow | Out-Null
        Write-Host "Regla de firewall creada" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠ No se pudo crear regla de firewall (requiere permisos de administrador)" -ForegroundColor Yellow
    }
}
else {
    Write-Host "Regla de firewall ya existe" -ForegroundColor Green
}

Write-Host ""

# Paso 6: Instalar auto-deploy
Write-Host "Instalando servicio de auto-deploy..." -ForegroundColor Yellow
& ".\auto_deploy_windows.ps1" -Install

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  INSTALACION COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Proximos pasos:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Editar .env con tus credenciales (si no lo has hecho):" -ForegroundColor Yellow
Write-Host "   notepad .env" -ForegroundColor White
Write-Host ""
Write-Host "2. Iniciar la aplicacion manualmente (primera vez):" -ForegroundColor Yellow
Write-Host "   .\iniciar_produccion.ps1" -ForegroundColor White
Write-Host ""
Write-Host "3. Iniciar auto-deploy:" -ForegroundColor Yellow
Write-Host "   .\auto_deploy_windows.ps1 -Start" -ForegroundColor White
Write-Host ""
Write-Host "4. Verificar que funciona:" -ForegroundColor Yellow
Write-Host "   http://localhost:5000" -ForegroundColor White
Write-Host "   o" -ForegroundColor White
Write-Host "   http://10.0.2.64:5000" -ForegroundColor White
Write-Host ""
Write-Host "Comandos utiles:" -ForegroundColor Cyan
Write-Host "  .\auto_deploy_windows.ps1 -Status    # Ver estado" -ForegroundColor White
Write-Host "  .\auto_deploy_windows.ps1 -Stop      # Detener" -ForegroundColor White
Write-Host ""

Pop-Location

# Preguntar si quiere iniciar ahora
Write-Host ""
$start = Read-Host "¿Iniciar auto-deploy ahora? (S/N)"
if ($start -eq "S" -or $start -eq "s") {
    Write-Host ""
    Write-Host "Iniciando auto-deploy..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$REPO_PATH\auto_deploy_windows.ps1`" -Start"
    Start-Sleep -Seconds 2
    Write-Host ""
    Write-Host "Auto-deploy iniciado en segundo plano" -ForegroundColor Green
    Write-Host ""
    Write-Host "Ver estado:" -ForegroundColor Yellow
    Write-Host "  .\auto_deploy_windows.ps1 -Status" -ForegroundColor White
    Write-Host ""
}

Write-Host "Instalacion completa. El auto-deploy se iniciara automaticamente al arrancar Windows" -ForegroundColor Green
Write-Host ""
