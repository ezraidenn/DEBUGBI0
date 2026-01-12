# ============================================
# Script de Instalacion Completa - Windows
# BioStar Monitor Auto-Deploy
# ============================================

param(
    [string]$ServerUser = "",
    [string]$ServerIP = "10.0.2.64"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BioStar Monitor - Instalacion Completa" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path ".git")) {
    Write-Host "ERROR: Debes ejecutar este script desde el directorio del repositorio" -ForegroundColor Red
    exit 1
}

# Solicitar usuario del servidor si no se proporciono
if ($ServerUser -eq "") {
    Write-Host "Ingresa el usuario SSH del servidor (ejemplo: administrador, root, etc.):" -ForegroundColor Yellow
    $ServerUser = Read-Host "Usuario"
}

Write-Host ""
Write-Host "Configuracion:" -ForegroundColor Cyan
Write-Host "  Servidor: $ServerIP" -ForegroundColor Yellow
Write-Host "  Usuario: $ServerUser" -ForegroundColor Yellow
Write-Host ""

# Confirmar
$confirm = Read-Host "¿Continuar con la instalacion? (S/N)"
if ($confirm -ne "S" -and $confirm -ne "s") {
    Write-Host "Instalacion cancelada" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Paso 1: Preparando archivos locales" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Agregar archivos al repositorio
Write-Host "Agregando archivos nuevos al repositorio..." -ForegroundColor Yellow
git add .
git commit -m "feat: Agregar scripts de instalacion automatizada completa" -ErrorAction SilentlyContinue

# Push a GitHub
Write-Host "Subiendo cambios a GitHub..." -ForegroundColor Yellow
git push origin main

Write-Host "✓ Archivos preparados y subidos a GitHub" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Paso 2: Conectando al servidor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Crear script temporal para ejecutar en el servidor
$remoteScript = @"
#!/bin/bash
set -e

echo '=========================================='
echo '  Clonando repositorio...'
echo '=========================================='

cd /tmp
if [ -d "DEBUGBI0" ]; then
    echo 'Eliminando repositorio anterior...'
    rm -rf DEBUGBI0
fi

git clone https://github.com/ezraidenn/DEBUGBI0.git
cd DEBUGBI0

echo ''
echo '=========================================='
echo '  Ejecutando instalacion completa...'
echo '=========================================='
echo ''

chmod +x deployment/install_complete.sh
sudo ./deployment/install_complete.sh

echo ''
echo '=========================================='
echo '  INSTALACION COMPLETADA'
echo '=========================================='
echo ''
"@

# Guardar script temporal
$remoteScript | Out-File -FilePath ".\temp_install.sh" -Encoding ASCII -NoNewline

Write-Host "Copiando script de instalacion al servidor..." -ForegroundColor Yellow
scp .\temp_install.sh ${ServerUser}@${ServerIP}:/tmp/install_biostar.sh

Write-Host "Ejecutando instalacion en el servidor..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  EJECUTANDO EN SERVIDOR" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

ssh ${ServerUser}@${ServerIP} "chmod +x /tmp/install_biostar.sh && /tmp/install_biostar.sh"

# Limpiar archivo temporal
Remove-Item .\temp_install.sh -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ INSTALACION COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "IMPORTANTE: Ahora debes configurar GitHub Secrets" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. La clave SSH privada se mostro en el servidor" -ForegroundColor Cyan
Write-Host "2. Ve a: https://github.com/ezraidenn/DEBUGBI0/settings/secrets/actions" -ForegroundColor Cyan
Write-Host "3. Crea estos 3 secrets:" -ForegroundColor Cyan
Write-Host "   - SSH_PRIVATE_KEY: (copia la clave del servidor)" -ForegroundColor Yellow
Write-Host "   - SERVER_HOST: 10.0.2.64" -ForegroundColor Yellow
Write-Host "   - SERVER_USER: deploy" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Haz un push a main para activar el auto-deploy:" -ForegroundColor Cyan
Write-Host "   git add ." -ForegroundColor Yellow
Write-Host "   git commit -m 'test: Activar auto-deploy'" -ForegroundColor Yellow
Write-Host "   git push origin main" -ForegroundColor Yellow
Write-Host ""
Write-Host "5. Monitorea en: https://github.com/ezraidenn/DEBUGBI0/actions" -ForegroundColor Cyan
Write-Host ""
Write-Host "6. Verifica en: http://10.0.2.64" -ForegroundColor Cyan
Write-Host ""

# Preguntar si quiere abrir GitHub
$openGitHub = Read-Host "¿Abrir GitHub Secrets en el navegador? (S/N)"
if ($openGitHub -eq "S" -or $openGitHub -eq "s") {
    Start-Process "https://github.com/ezraidenn/DEBUGBI0/settings/secrets/actions"
}

Write-Host ""
Write-Host "Instalacion completa. El servidor esta listo para recibir deployments automaticos." -ForegroundColor Green
Write-Host ""
