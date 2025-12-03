# Script de instalación para LOGSCHECA
# BioStar Debug Monitor

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INSTALACIÓN - LOGSCHECA" -ForegroundColor Cyan
Write-Host "BioStar Debug Monitor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Python
Write-Host "Verificando Python..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python no está instalado o no está en el PATH" -ForegroundColor Red
    Write-Host "Descarga Python desde: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""

# Crear entorno virtual
Write-Host "Creando entorno virtual..." -ForegroundColor Cyan
if (Test-Path "venv") {
    Write-Host "⚠ El entorno virtual ya existe" -ForegroundColor Yellow
    $response = Read-Host "¿Deseas recrearlo? (S/N)"
    
    if ($response -eq "S" -or $response -eq "s") {
        Write-Host "Eliminando entorno virtual existente..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force venv
    } else {
        Write-Host "Usando entorno virtual existente" -ForegroundColor Yellow
    }
}

if (-not (Test-Path "venv")) {
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Entorno virtual creado" -ForegroundColor Green
    } else {
        Write-Host "ERROR: No se pudo crear el entorno virtual" -ForegroundColor Red
        Read-Host "Presiona Enter para salir"
        exit 1
    }
}

Write-Host ""

# Activar entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

Write-Host "✓ Entorno virtual activado" -ForegroundColor Green
Write-Host ""

# Actualizar pip
Write-Host "Actualizando pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip --quiet
Write-Host "✓ pip actualizado" -ForegroundColor Green
Write-Host ""

# Instalar dependencias
Write-Host "Instalando dependencias..." -ForegroundColor Cyan
Write-Host "Esto puede tardar varios minutos..." -ForegroundColor Yellow
Write-Host ""

pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Dependencias instaladas correctamente" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "⚠ Hubo algunos errores durante la instalación" -ForegroundColor Yellow
    Write-Host "Revisa los mensajes anteriores para más detalles" -ForegroundColor Yellow
}

Write-Host ""

# Verificar archivo .env
Write-Host "Verificando configuración..." -ForegroundColor Cyan
if (-not (Test-Path ".env")) {
    Write-Host "⚠ Archivo .env no encontrado" -ForegroundColor Yellow
    Write-Host "Copiando .env.example a .env..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✓ Archivo .env creado" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANTE: Edita el archivo .env con tus credenciales de BioStar 2" -ForegroundColor Yellow
} else {
    Write-Host "✓ Archivo .env existe" -ForegroundColor Green
}

Write-Host ""

# Crear directorios necesarios
Write-Host "Creando directorios..." -ForegroundColor Cyan
if (-not (Test-Path "data\outputs")) {
    New-Item -ItemType Directory -Path "data\outputs" -Force | Out-Null
    Write-Host "✓ Directorio data/outputs creado" -ForegroundColor Green
}
if (-not (Test-Path "instance")) {
    New-Item -ItemType Directory -Path "instance" -Force | Out-Null
    Write-Host "✓ Directorio instance creado" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INSTALACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Edita el archivo .env con tus credenciales:" -ForegroundColor White
Write-Host "   notepad .env" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Configura el firewall (ejecutar como Administrador):" -ForegroundColor White
Write-Host "   .\configurar_firewall.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Inicia el servidor:" -ForegroundColor White
Write-Host "   python run_webapp.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Accede desde tu navegador:" -ForegroundColor White
Write-Host "   http://localhost:5000" -ForegroundColor Yellow
Write-Host "   http://10.0.0.10:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Credenciales por defecto:" -ForegroundColor White
Write-Host "   Usuario: admin" -ForegroundColor Yellow
Write-Host "   Contraseña: admin123" -ForegroundColor Yellow
Write-Host ""

Read-Host "Presiona Enter para salir"
