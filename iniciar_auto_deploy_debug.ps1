# Auto-Deploy con DEBUG - Muestra todo lo que hace

$REPO_PATH = "C:\Users\Administrador\Documents\DebugBi0\DEBUGBI0"
$CHECK_INTERVAL = 20  # 20 segundos para pruebas rapidas
$LOG_FILE = "$REPO_PATH\logs\autodeploy_debug.log"

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $LOG_FILE -Value $logMessage
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Auto-Deploy DEBUG Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repositorio: $REPO_PATH" -ForegroundColor Yellow
Write-Host "Intervalo: $CHECK_INTERVAL segundos" -ForegroundColor Yellow
Write-Host "Log: $LOG_FILE" -ForegroundColor Yellow
Write-Host "Presiona Ctrl+C para detener" -ForegroundColor Yellow
Write-Host ""

# Crear directorio de logs si no existe
if (-not (Test-Path "$REPO_PATH\logs")) {
    New-Item -ItemType Directory -Path "$REPO_PATH\logs" -Force | Out-Null
}

Push-Location $REPO_PATH

# Obtener commit actual
$lastCommit = git rev-parse HEAD
Write-Log "=== INICIO AUTO-DEPLOY ===" "Cyan"
Write-Log "Commit inicial: $lastCommit" "Green"
Write-Log "Monitoreando: https://github.com/ezraidenn/DEBUGBI0" "Yellow"
Write-Host ""

$iteration = 0
while ($true) {
    try {
        $iteration++
        $timestamp = Get-Date -Format "HH:mm:ss"
        
        Write-Host "[$timestamp] Iteracion #$iteration - Verificando..." -ForegroundColor Gray
        Write-Log "Iteracion #$iteration - Ejecutando git fetch..." "Gray"
        
        # Verificar cambios en GitHub
        $fetchOutput = git fetch origin main 2>&1
        Write-Log "Fetch completado: $fetchOutput" "Gray"
        
        $remoteCommit = git rev-parse origin/main
        Write-Log "Commit local: $lastCommit" "Gray"
        Write-Log "Commit remoto: $remoteCommit" "Gray"
        
        if ($remoteCommit -ne $lastCommit) {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Yellow
            Write-Host "  ¡NUEVO COMMIT DETECTADO!" -ForegroundColor Yellow
            Write-Host "========================================" -ForegroundColor Yellow
            Write-Log "=== NUEVO COMMIT DETECTADO ===" "Yellow"
            Write-Log "Anterior: $lastCommit" "Gray"
            Write-Log "Nuevo: $remoteCommit" "Green"
            
            # Actualizar repositorio
            Write-Host "Descargando cambios..." -ForegroundColor Cyan
            Write-Log "Ejecutando git pull..." "Cyan"
            $pullOutput = git pull origin main
            Write-Log "Pull output: $pullOutput" "Gray"
            
            # Detener procesos Python
            Write-Host "Deteniendo aplicacion..." -ForegroundColor Cyan
            Write-Log "Deteniendo procesos Python..." "Cyan"
            try {
                $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
                if ($pythonProcesses) {
                    $pythonProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
                    Write-Host "  Procesos Python detenidos ($($pythonProcesses.Count))" -ForegroundColor Gray
                    Write-Log "Procesos detenidos: $($pythonProcesses.Count)" "Gray"
                } else {
                    Write-Host "  No hay procesos Python corriendo" -ForegroundColor Gray
                    Write-Log "No hay procesos Python" "Gray"
                }
            }
            catch {
                Write-Host "  Error al detener: $_" -ForegroundColor Yellow
                Write-Log "Error deteniendo procesos: $_" "Red"
            }
            
            Start-Sleep -Seconds 3
            
            # Reiniciar aplicacion
            Write-Host "Reiniciando aplicacion..." -ForegroundColor Cyan
            Write-Log "Iniciando nueva instancia de la aplicacion..." "Cyan"
            Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoExit -Command `"cd '$REPO_PATH'; python run_production.py`"" -WindowStyle Normal
            Write-Log "Aplicacion reiniciada" "Green"
            
            $lastCommit = $remoteCommit
            
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "  DEPLOY COMPLETADO" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Log "=== DEPLOY COMPLETADO ===" "Green"
            Write-Host ""
        }
        else {
            # Mostrar progreso cada 3 iteraciones
            if ($iteration % 3 -eq 0) {
                Write-Host "." -NoNewline
            }
        }
        
        Write-Log "Esperando $CHECK_INTERVAL segundos..." "Gray"
        Start-Sleep -Seconds $CHECK_INTERVAL
    }
    catch {
        Write-Host "ERROR: $_" -ForegroundColor Red
        Write-Log "ERROR CRITICO: $_" "Red"
        Start-Sleep -Seconds $CHECK_INTERVAL
    }
}

Pop-Location
