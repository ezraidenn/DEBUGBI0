# ============================================
# Auto-Deploy para Windows Server
# Detecta cambios en GitHub y actualiza automaticamente
# ============================================

param(
    [switch]$Install,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Status,
    [int]$CheckInterval = 60  # Segundos entre verificaciones
)

$ErrorActionPreference = "Stop"

# Configuracion
$REPO_PATH = "C:\Users\Administrador\Documents\DebugBi0\DEBUGBI0"
$REPO_URL = "https://github.com/ezraidenn/DEBUGBI0.git"
$APP_SCRIPT = "iniciar_produccion.ps1"
$LOG_FILE = "$REPO_PATH\logs\auto_deploy.log"
$PID_FILE = "$REPO_PATH\auto_deploy.pid"
$LAST_COMMIT_FILE = "$REPO_PATH\.last_commit"

# Colores
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Add-Content -Path $LOG_FILE -Value $logMessage
    Write-Host $logMessage
}

function Get-RemoteCommit {
    try {
        Push-Location $REPO_PATH
        git fetch origin main 2>&1 | Out-Null
        $commit = git rev-parse origin/main
        Pop-Location
        return $commit
    }
    catch {
        Write-Log "ERROR: No se pudo obtener commit remoto: $_"
        Pop-Location
        return $null
    }
}

function Get-LocalCommit {
    try {
        Push-Location $REPO_PATH
        $commit = git rev-parse HEAD
        Pop-Location
        return $commit
    }
    catch {
        Write-Log "ERROR: No se pudo obtener commit local: $_"
        Pop-Location
        return $null
    }
}

function Update-Repository {
    Write-Log "Actualizando repositorio desde GitHub..."
    try {
        Push-Location $REPO_PATH
        
        # Guardar cambios locales si existen
        git stash 2>&1 | Out-Null
        
        # Pull cambios
        git pull origin main
        
        Write-Log "✓ Repositorio actualizado exitosamente"
        Pop-Location
        return $true
    }
    catch {
        Write-Log "ERROR: Fallo al actualizar repositorio: $_"
        Pop-Location
        return $false
    }
}

function Restart-Application {
    Write-Log "Reiniciando aplicacion..."
    try {
        # Detener proceso actual si existe
        $processes = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
            $_.Path -like "*$REPO_PATH*"
        }
        
        if ($processes) {
            Write-Log "Deteniendo procesos existentes..."
            $processes | Stop-Process -Force
            Start-Sleep -Seconds 2
        }
        
        # Iniciar aplicacion
        Push-Location $REPO_PATH
        Start-Process powershell -ArgumentList "-File `"$REPO_PATH\$APP_SCRIPT`"" -WindowStyle Hidden
        Pop-Location
        
        Write-Log "✓ Aplicacion reiniciada exitosamente"
        return $true
    }
    catch {
        Write-Log "ERROR: Fallo al reiniciar aplicacion: $_"
        Pop-Location
        return $false
    }
}

function Start-AutoDeploy {
    Write-ColorOutput Green "=========================================="
    Write-ColorOutput Green "  Auto-Deploy Windows - INICIANDO"
    Write-ColorOutput Green "=========================================="
    Write-Host ""
    
    # Crear directorio de logs si no existe
    $logsDir = Split-Path $LOG_FILE -Parent
    if (-not (Test-Path $logsDir)) {
        New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    }
    
    Write-Log "Auto-Deploy iniciado. Intervalo de verificacion: $CheckInterval segundos"
    Write-Log "Repositorio: $REPO_URL"
    Write-Log "Ruta local: $REPO_PATH"
    
    # Guardar PID
    $PID | Out-File -FilePath $PID_FILE -Force
    
    # Obtener commit inicial
    $lastCommit = Get-LocalCommit
    $lastCommit | Out-File -FilePath $LAST_COMMIT_FILE -Force
    Write-Log "Commit actual: $lastCommit"
    
    Write-Host ""
    Write-ColorOutput Cyan "Monitoreando cambios en GitHub..."
    Write-Host "Presiona Ctrl+C para detener"
    Write-Host ""
    
    $checkCount = 0
    while ($true) {
        try {
            $checkCount++
            
            # Verificar commit remoto
            $remoteCommit = Get-RemoteCommit
            
            if ($remoteCommit -and $remoteCommit -ne $lastCommit) {
                Write-Host ""
                Write-ColorOutput Yellow "=========================================="
                Write-ColorOutput Yellow "  NUEVO COMMIT DETECTADO"
                Write-ColorOutput Yellow "=========================================="
                Write-Log "Nuevo commit detectado: $remoteCommit"
                Write-Log "Commit anterior: $lastCommit"
                
                # Actualizar repositorio
                if (Update-Repository) {
                    # Reiniciar aplicacion
                    if (Restart-Application) {
                        $lastCommit = $remoteCommit
                        $lastCommit | Out-File -FilePath $LAST_COMMIT_FILE -Force
                        
                        Write-Host ""
                        Write-ColorOutput Green "=========================================="
                        Write-ColorOutput Green "  ✓ DEPLOY COMPLETADO"
                        Write-ColorOutput Green "=========================================="
                        Write-Host ""
                    }
                    else {
                        Write-ColorOutput Red "✗ Error al reiniciar aplicacion"
                    }
                }
                else {
                    Write-ColorOutput Red "✗ Error al actualizar repositorio"
                }
            }
            else {
                # Mostrar progreso cada 10 verificaciones
                if ($checkCount % 10 -eq 0) {
                    Write-Host "." -NoNewline
                }
            }
            
            # Esperar antes de la siguiente verificacion
            Start-Sleep -Seconds $CheckInterval
        }
        catch {
            Write-Log "ERROR en ciclo principal: $_"
            Start-Sleep -Seconds $CheckInterval
        }
    }
}

function Stop-AutoDeploy {
    Write-ColorOutput Yellow "Deteniendo Auto-Deploy..."
    
    if (Test-Path $PID_FILE) {
        $pid = Get-Content $PID_FILE
        try {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Remove-Item $PID_FILE -Force
            Write-ColorOutput Green "✓ Auto-Deploy detenido"
        }
        catch {
            Write-ColorOutput Red "✗ No se pudo detener el proceso (PID: $pid)"
        }
    }
    else {
        Write-ColorOutput Yellow "Auto-Deploy no esta en ejecucion"
    }
}

function Show-Status {
    Write-Host ""
    Write-ColorOutput Cyan "=========================================="
    Write-ColorOutput Cyan "  Estado de Auto-Deploy"
    Write-ColorOutput Cyan "=========================================="
    Write-Host ""
    
    # Verificar si esta corriendo
    if (Test-Path $PID_FILE) {
        $pid = Get-Content $PID_FILE
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        
        if ($process) {
            Write-ColorOutput Green "Estado: EJECUTANDOSE"
            Write-Host "PID: $pid"
        }
        else {
            Write-ColorOutput Red "Estado: DETENIDO (PID file obsoleto)"
            Remove-Item $PID_FILE -Force
        }
    }
    else {
        Write-ColorOutput Yellow "Estado: DETENIDO"
    }
    
    # Mostrar ultimo commit
    if (Test-Path $LAST_COMMIT_FILE) {
        $lastCommit = Get-Content $LAST_COMMIT_FILE
        Write-Host "Ultimo commit: $lastCommit"
    }
    
    # Mostrar ultimas lineas del log
    if (Test-Path $LOG_FILE) {
        Write-Host ""
        Write-ColorOutput Cyan "Ultimas 10 lineas del log:"
        Get-Content $LOG_FILE -Tail 10
    }
    
    Write-Host ""
}

function Install-AutoDeploy {
    Write-ColorOutput Cyan "=========================================="
    Write-ColorOutput Cyan "  Instalando Auto-Deploy"
    Write-ColorOutput Cyan "=========================================="
    Write-Host ""
    
    # Crear tarea programada de Windows
    $taskName = "BioStarMonitor-AutoDeploy"
    $scriptPath = $PSCommandPath
    
    # Eliminar tarea existente
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    
    # Crear accion
    $action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`" -Start"
    
    # Crear trigger (al inicio del sistema)
    $trigger = New-ScheduledTaskTrigger -AtStartup
    
    # Crear configuracion
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -StartWhenAvailable -RunOnlyIfNetworkAvailable
    
    # Registrar tarea
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
        -Settings $settings -Description "Auto-Deploy para BioStar Monitor" `
        -User $env:USERNAME -RunLevel Highest
    
    Write-ColorOutput Green "✓ Tarea programada creada: $taskName"
    Write-Host ""
    Write-ColorOutput Yellow "El auto-deploy se iniciara automaticamente al arrancar Windows"
    Write-Host ""
}

# ============================================
# MAIN
# ============================================

if ($Install) {
    Install-AutoDeploy
}
elseif ($Start) {
    Start-AutoDeploy
}
elseif ($Stop) {
    Stop-AutoDeploy
}
elseif ($Status) {
    Show-Status
}
else {
    Write-Host ""
    Write-ColorOutput Cyan "=========================================="
    Write-ColorOutput Cyan "  Auto-Deploy para Windows Server"
    Write-ColorOutput Cyan "=========================================="
    Write-Host ""
    Write-Host "Uso:"
    Write-Host "  .\auto_deploy_windows.ps1 -Install    # Instalar como servicio"
    Write-Host "  .\auto_deploy_windows.ps1 -Start      # Iniciar monitoreo"
    Write-Host "  .\auto_deploy_windows.ps1 -Stop       # Detener monitoreo"
    Write-Host "  .\auto_deploy_windows.ps1 -Status     # Ver estado"
    Write-Host ""
    Write-Host "Opciones:"
    Write-Host "  -CheckInterval <segundos>  # Intervalo de verificacion (default: 60)"
    Write-Host ""
    Write-Host "Ejemplos:"
    Write-Host "  .\auto_deploy_windows.ps1 -Start -CheckInterval 30"
    Write-Host "  .\auto_deploy_windows.ps1 -Install"
    Write-Host ""
}
