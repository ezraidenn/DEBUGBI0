# Auto-Deploy Simple para Windows
# Monitorea GitHub y actualiza automaticamente

$REPO_PATH = "C:\Users\Administrador\Documents\DebugBi0\DEBUGBI0"
$CHECK_INTERVAL = 60  # segundos

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Auto-Deploy Iniciado" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Monitoreando: https://github.com/ezraidenn/DEBUGBI0" -ForegroundColor Yellow
Write-Host "Intervalo: $CHECK_INTERVAL segundos" -ForegroundColor Yellow
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
            try {
                $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
                if ($pythonProcesses) {
                    $pythonProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
                    Write-Host "  Procesos Python detenidos" -ForegroundColor Gray
                } else {
                    Write-Host "  No hay procesos Python corriendo" -ForegroundColor Gray
                }
            }
            catch {
                Write-Host "  Error al detener procesos: $_" -ForegroundColor Yellow
            }
            
            Start-Sleep -Seconds 3
            
            # Reiniciar aplicacion
            Write-Host "Reiniciando aplicacion..." -ForegroundColor Cyan
            Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$REPO_PATH\iniciar_produccion.ps1`"" -WindowStyle Hidden
            
            $lastCommit = $remoteCommit
            
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "  DEPLOY COMPLETADO" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
        }
        else {
            # Mostrar progreso
            if ($count % 10 -eq 0) {
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
