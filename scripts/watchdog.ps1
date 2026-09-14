<#
.SYNOPSIS
    DEBUGBI0 - supervisor de la webapp.

.DESCRIPTION
    Mantiene run.py corriendo: lo arranca si no esta vivo y lo relanza cuando
    termina (con backoff si se cae en bucle). Lo ejecuta la tarea programada
    "DEBUGBI0-Webapp" (ver scripts\install-task.ps1), pero tambien corre a mano.

    Si la app ya esta arriba (lanzada a mano o por otra instancia del watchdog)
    NO levanta una segunda: se queda esperando a que ese proceso muera. Asi se
    evita el choque de puerto con start.bat / start.ps1.

    OJO con el arbol de procesos: el servidor de desarrollo de Werkzeug lanza un
    proceso hijo (el recargador) y es EL HIJO quien abre el puerto. Si el padre
    muere, el hijo puede quedar huerfano ocupando el puerto y el siguiente
    arranque fallaria. Por eso se limpia el arbol completo antes de cada
    arranque y despues de cada salida.

.PARAMETER Once
    Arranca la app si no corre y sale, sin supervisar. Util para probar.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\watchdog.ps1 -Once
#>
[CmdletBinding()]
param(
    [int]$RestartDelaySeconds = 10,
    [int]$MaxBackoffSeconds = 300,
    [switch]$Once
)

$ErrorActionPreference = 'Stop'

$Root        = Split-Path -Parent $PSScriptRoot
$Python      = Join-Path $Root 'venv\Scripts\python.exe'
$Entry       = Join-Path $Root 'run.py'
$LogDir      = Join-Path $Root 'logs'
$LogFile     = Join-Path $LogDir 'watchdog.log'
$OutFile     = Join-Path $LogDir 'webapp.out.log'
$ErrFile     = Join-Path $LogDir 'webapp.err.log'
$MaxLogBytes = 5MB

if (-not (Test-Path -LiteralPath $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Invoke-LogRotation {
    param([Parameter(Mandatory)][string]$Path)
    if ((Test-Path -LiteralPath $Path) -and ((Get-Item -LiteralPath $Path).Length -gt $MaxLogBytes)) {
        Move-Item -LiteralPath $Path -Destination "$Path.1" -Force
    }
}

function Write-Log {
    param(
        [Parameter(Mandatory)][string]$Message,
        [ValidateSet('INFO', 'WARN', 'ERROR')][string]$Level = 'INFO'
    )
    $line = '{0} | {1} | [WATCHDOG] {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Level, $Message
    try {
        Invoke-LogRotation -Path $LogFile
        Add-Content -LiteralPath $LogFile -Value $line -Encoding utf8
    }
    catch {
        # Nunca dejar que un fallo de log tumbe al supervisor.
    }
    Write-Output $line
}

function Get-AppProcesses {
    <# Procesos que corren ESTE run.py (no el de otros proyectos del servidor). #>
    @(
        Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -and $_.CommandLine -like "*$Entry*" }
    )
}

function Get-AppRootProcess {
    <# El padre del arbol: el unico cuyo padre no es tambien proceso de la app. #>
    $all = Get-AppProcesses
    if ($all.Count -eq 0) { return $null }
    $ids = @($all | ForEach-Object { $_.ProcessId })
    $root = $all | Where-Object { $ids -notcontains $_.ParentProcessId } | Select-Object -First 1
    if ($root) { return $root }
    return $all[0]
}

function Stop-AppTree {
    <# Mata cualquier resto de la app para dejar el puerto libre. #>
    param([string]$Reason = 'limpieza')
    foreach ($p in Get-AppProcesses) {
        try {
            Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
            Write-Log "Proceso $($p.ProcessId) eliminado ($Reason)." 'WARN'
        }
        catch {
            # Ya habia muerto por su cuenta.
        }
    }
}

function Start-App {
    Stop-AppTree -Reason 'resto de un arranque anterior'
    Invoke-LogRotation -Path $OutFile
    Invoke-LogRotation -Path $ErrFile
    Start-Process -FilePath $Python -ArgumentList $Entry `
        -WorkingDirectory $Root -NoNewWindow -PassThru `
        -RedirectStandardOutput $OutFile -RedirectStandardError $ErrFile
}

# ---- Preflight -------------------------------------------------------------
foreach ($required in @($Python, $Entry, (Join-Path $Root '.env'))) {
    if (-not (Test-Path -LiteralPath $required)) {
        Write-Log "Falta '$required'. No se puede arrancar." 'ERROR'
        exit 1
    }
}

# ---- Modo disparo unico ----------------------------------------------------
if ($Once) {
    $running = Get-AppRootProcess
    if ($running) {
        Write-Log "La app ya corre (PID $($running.ProcessId)). Nada que hacer."
        exit 0
    }
    $proc = Start-App
    Write-Log "App arrancada (PID $($proc.Id)) en modo -Once."
    exit 0
}

# ---- Supervisor ------------------------------------------------------------
Write-Log "Supervisor iniciado (PID $PID, root=$Root)."
$consecutiveFailures = 0

while ($true) {
    $running = Get-AppRootProcess

    if ($running) {
        Write-Log "La app ya corre (PID $($running.ProcessId)); no se levanta otra. Esperando."
        try { Wait-Process -Id $running.ProcessId -ErrorAction Stop } catch { }
        Write-Log "El proceso $($running.ProcessId) termino." 'WARN'
        $consecutiveFailures = 0
    }
    else {
        $startedAt = Get-Date
        $proc = $null
        try {
            $proc = Start-App
        }
        catch {
            Write-Log "No se pudo arrancar: $($_.Exception.Message)" 'ERROR'
        }

        if ($proc) {
            Write-Log "App arrancada (PID $($proc.Id))."
            $proc.WaitForExit()
            $uptime = (Get-Date) - $startedAt

            # Un proceso terminado a la fuerza puede no exponer ExitCode.
            $exitCode = 'desconocido'
            try { if ($null -ne $proc.ExitCode) { $exitCode = $proc.ExitCode } } catch { }
            Write-Log ('App termino con codigo {0} tras {1:n0}s.' -f $exitCode, $uptime.TotalSeconds) 'WARN'

            # Solo cuenta como fallo si murio rapido: un cierre tras horas de
            # servicio no debe meter backoff.
            if ($uptime.TotalSeconds -ge 60) { $consecutiveFailures = 0 } else { $consecutiveFailures++ }
        }
        else {
            $consecutiveFailures++
        }
    }

    # El hijo recargador sobrevive al padre: sin esto el puerto seguiria ocupado.
    Stop-AppTree -Reason 'huerfano tras la salida del proceso principal'

    $delay = [Math]::Min(
        $RestartDelaySeconds * [Math]::Pow(2, [Math]::Min($consecutiveFailures, 6)),
        $MaxBackoffSeconds
    )
    if ($consecutiveFailures -gt 0) {
        Write-Log "Fallo rapido #$consecutiveFailures; reintento en $delay s. Revisa logs\webapp.err.log." 'WARN'
    }
    Start-Sleep -Seconds $delay
}
