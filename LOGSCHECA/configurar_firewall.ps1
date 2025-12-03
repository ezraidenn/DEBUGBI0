# Script para configurar el Firewall de Windows para LOGSCHECA
# Ejecutar como Administrador

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Configuración de Firewall - LOGSCHECA" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si se está ejecutando como administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: Este script debe ejecutarse como Administrador" -ForegroundColor Red
    Write-Host "Haz clic derecho en PowerShell y selecciona 'Ejecutar como administrador'" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host "✓ Ejecutando como Administrador" -ForegroundColor Green
Write-Host ""

# Nombre de la regla
$ruleName = "BioStar Monitor - Puerto 5000"

# Verificar si la regla ya existe
$existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue

if ($existingRule) {
    Write-Host "⚠ La regla de firewall ya existe" -ForegroundColor Yellow
    $response = Read-Host "¿Deseas eliminarla y recrearla? (S/N)"
    
    if ($response -eq "S" -or $response -eq "s") {
        Write-Host "Eliminando regla existente..." -ForegroundColor Yellow
        Remove-NetFirewallRule -DisplayName $ruleName
        Write-Host "✓ Regla eliminada" -ForegroundColor Green
    } else {
        Write-Host "Operación cancelada" -ForegroundColor Yellow
        Read-Host "Presiona Enter para salir"
        exit 0
    }
}

# Crear nueva regla de firewall
Write-Host ""
Write-Host "Creando regla de firewall..." -ForegroundColor Cyan

try {
    New-NetFirewallRule `
        -DisplayName $ruleName `
        -Description "Permite conexiones entrantes al servidor BioStar Monitor en el puerto 5000" `
        -Direction Inbound `
        -LocalPort 5000 `
        -Protocol TCP `
        -Action Allow `
        -Enabled True `
        -Profile Any `
        -ErrorAction Stop
    
    Write-Host "✓ Regla de firewall creada exitosamente" -ForegroundColor Green
} catch {
    Write-Host "ERROR: No se pudo crear la regla de firewall" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar la regla
Write-Host ""
Write-Host "Verificando configuración..." -ForegroundColor Cyan
$rule = Get-NetFirewallRule -DisplayName $ruleName

if ($rule) {
    Write-Host "✓ Regla verificada correctamente" -ForegroundColor Green
    Write-Host ""
    Write-Host "Detalles de la regla:" -ForegroundColor Cyan
    Write-Host "  Nombre: $($rule.DisplayName)" -ForegroundColor White
    Write-Host "  Estado: $($rule.Enabled)" -ForegroundColor White
    Write-Host "  Dirección: $($rule.Direction)" -ForegroundColor White
    Write-Host "  Acción: $($rule.Action)" -ForegroundColor White
} else {
    Write-Host "⚠ No se pudo verificar la regla" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Configuración completada" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "El servidor ahora puede aceptar conexiones en el puerto 5000 desde:" -ForegroundColor White
Write-Host "  - localhost (127.0.0.1)" -ForegroundColor White
Write-Host "  - Red local (10.0.0.10)" -ForegroundColor White
Write-Host "  - Cualquier otra IP en la red" -ForegroundColor White
Write-Host ""
Write-Host "Para iniciar el servidor, ejecuta:" -ForegroundColor Cyan
Write-Host "  python run_webapp.py" -ForegroundColor Yellow
Write-Host ""

Read-Host "Presiona Enter para salir"
