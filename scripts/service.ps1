<#
.SYNOPSIS
    Control manual de la webapp DEBUGBI0 gestionada por la tarea "DEBUGBI0-Webapp".

.DESCRIPTION
    start    Arranca la tarea (y con ella el supervisor + la app).
    stop     Detiene la tarea Y mata la app. Es la unica forma de bajarla de
             verdad: si matas solo el python, el supervisor lo vuelve a subir.
    restart  stop + start.
    status   Estado de la tarea, PID de la app, puerto a la escucha y ultimas
             lineas del log del supervisor.
    logs     Sigue en vivo logs\watchdog.log (Ctrl+C para salir).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\service.ps1 status
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'logs')]
    [string]$Action = 'status',

    [string]$TaskName = 'DEBUGBI0-Webapp'
)

$ErrorActionPreference = 'Stop'

$Root        = Split-Path -Parent $PSScriptRoot
$Entry       = Join-Path $Root 'run.py'
$WatchdogLog = Join-Path $Root 'logs\watchdog.log'

function Get-AppProcess {
    Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine -like "*$Entry*" }
}

function Get-EnvValue {
    param([string]$Key, [string]$Default)
    $envFile = Join-Path $Root '.env'
    if (Test-Path -LiteralPath $envFile) {
        $match = Select-String -LiteralPath $envFile -Pattern "^$Key=(.*)$" | Select-Object -First 1
        if ($match) { return $match.Matches[0].Groups[1].Value.Trim() }
    }
    return $Default
}

function Assert-Task {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $task) {
        throw "La tarea '$TaskName' no existe. Registrala con: scripts\install-task.ps1"
    }
    return $task
}

switch ($Action) {

    'start' {
        Assert-Task | Out-Null
        Start-ScheduledTask -TaskName $TaskName
        Write-Output "Tarea '$TaskName' arrancada. Mira el estado con: scripts\service.ps1 status"
    }

    'stop' {
        if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
            Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
            Write-Output "Tarea '$TaskName' detenida."
        }
        # El supervisor ya no esta, pero la app es un proceso aparte: hay que
        # bajarla explicitamente o se queda ocupando el puerto.
        $procs = @(Get-AppProcess)
        if ($procs.Count -gt 0) {
            foreach ($p in $procs) {
                Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
                Write-Output "App detenida (PID $($p.ProcessId))."
            }
        }
        else {
            Write-Output "No habia proceso de la app corriendo."
        }
    }

    'restart' {
        & $PSCommandPath -Action stop -TaskName $TaskName
        & $PSCommandPath -Action start -TaskName $TaskName
    }

    'status' {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($task) {
            $info = Get-ScheduledTaskInfo -TaskName $TaskName
            Write-Output "Tarea:          $TaskName [$($task.State)]"
            Write-Output "  Ultima vez:   $($info.LastRunTime)  (resultado: $($info.LastTaskResult))"
            Write-Output "  Proxima vez:  $($info.NextRunTime)"
        }
        else {
            Write-Output "Tarea:          NO REGISTRADA (usa scripts\install-task.ps1)"
        }

        $procs = @(Get-AppProcess)
        if ($procs.Count -gt 0) {
            foreach ($p in $procs) { Write-Output "App:            CORRIENDO (PID $($p.ProcessId))" }
        }
        else {
            Write-Output "App:            DETENIDA"
        }

        $appHost = Get-EnvValue -Key 'HOST' -Default '127.0.0.1'
        $port    = [int](Get-EnvValue -Key 'PORT' -Default '5000')
        $listen  = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if ($listen) {
            Write-Output "Puerto $port :   a la escucha  ->  http://${appHost}:$port"
        }
        else {
            Write-Output "Puerto $port :   sin escucha"
        }

        if (Test-Path -LiteralPath $WatchdogLog) {
            Write-Output ""
            Write-Output "--- ultimas lineas de logs\watchdog.log ---"
            Get-Content -LiteralPath $WatchdogLog -Tail 10
        }
    }

    'logs' {
        if (-not (Test-Path -LiteralPath $WatchdogLog)) {
            throw "Todavia no existe '$WatchdogLog'."
        }
        Get-Content -LiteralPath $WatchdogLog -Tail 30 -Wait
    }
}
