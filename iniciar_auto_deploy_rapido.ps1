# Auto-Deploy Rapido para Windows (verifica cada 30 segundos)

$REPO_PATH = "C:\Users\Administrador\Documents\DebugBi0\DEBUGBI0"
$CHECK_INTERVAL = 30  # segundos (mas rapido)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Auto-Deploy RAPIDO Iniciado" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Monitoreando: https://github.com/ezraidenn/DEBUGBI0" -ForegroundColor Yellow
Write-Host "Intervalo: $CHECK_INTERVAL segundos (RAPIDO)" -ForegroundColor Green
Write-Host "Presiona Ctrl+C para detener" -ForegroundColor Yellow
Write-Host ""

Push-Location $REPO_PATH

# Obtener commit actual
$lastCommit = git rev-parse HEAD
Write-Host "Commit actual: $lastCommit" -ForegroundColor Green
Write-Host ""

$count = 0
while ($true) {
    try {
        $count++
        
        # Verificar cambios en GitHub
        git fetch origin main 2>&1 | Out-Null
        $remoteCommit = git rev-parse origin/main
        
        if ($remoteCommit -ne $lastCommit) {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Yellow
            Write-Host "  NUEVO COMMIT DETECTADO!" -ForegroundColor Yellow
            Write-Host "========================================" -ForegroundColor Yellow
            Write-Host "Anterior: $lastCommit" -ForegroundColor Gray
            Write-Host "Nuevo: $remoteCommit" -ForegroundColor Green
            Write-Host ""
            
            # Actualizar repositorio
            Write-Host "Descargando cambios..." -ForegroundColor Cyan
            git pull origin main
            
            # Detener procesos Python existentes
            Write-Host "Deteniendo aplicacion..." -ForegroundColor Cyan
            Get-Process python -ErrorAction SilentlyContinue | Where-Object {
                $_.Path -like "*$REPO_PATH*"
            } | Stop-Process -Force
            
            Start-Sleep -Seconds 2
            
            # Reiniciar aplicacion
            Write-Host "Reiniciando aplicacion..." -ForegroundColor Cyan
            Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoExit -Command `"cd '$REPO_PATH'; python run_production.py`"" -WindowStyle Normal
            
            $lastCommit = $remoteCommit
            
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "  DEPLOY COMPLETADO" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
        }
        else {
            # Mostrar progreso
            if ($count % 5 -eq 0) {
                Write-Host "." -NoNewline
            }
        }
        
        Start-Sleep -Seconds $CHECK_INTERVAL
    }
    catch {
        Write-Host "Error: $_" -ForegroundColor Red
        Start-Sleep -Seconds $CHECK_INTERVAL
    }
}

Pop-Location
