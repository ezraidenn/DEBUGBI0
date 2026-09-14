<#
.SYNOPSIS
    Registra (o quita) la tarea programada que mantiene viva la webapp DEBUGBI0.

.DESCRIPTION
    Crea la tarea "DEBUGBI0-Webapp", que ejecuta scripts\watchdog.ps1 con:

      * Trigger de arranque   -> vuelve sola despues de un reinicio o apagon,
                                 sin necesidad de que nadie inicie sesion.
      * Trigger cada 5 min    -> si el supervisor muere, la siguiente pasada lo
                                 revive. Con MultipleInstancesPolicy=IgnoreNew,
                                 mientras siga vivo esas pasadas no hacen nada.
      * Sin limite de tiempo  -> ExecutionTimeLimit=PT0S, la tarea vive siempre.
      * RestartOnFailure      -> 3 reintentos separados 1 min si la tarea falla.

    Corre como SYSTEM: no guarda contrasena y arranca en el boot aunque no haya
    sesion iniciada. La app solo toca rutas dentro del proyecto (SQLite + logs),
    asi que no necesita el perfil del usuario.

    Requiere consola elevada (Ejecutar como administrador).

.PARAMETER Uninstall
    Quita la tarea en lugar de crearla. No detiene la app que ya este corriendo.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\install-task.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\install-task.ps1 -Uninstall
#>
[CmdletBinding()]
param(
    [string]$TaskName = 'DEBUGBI0-Webapp',
    [int]$WatchdogIntervalMinutes = 5,
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'

$Root     = Split-Path -Parent $PSScriptRoot
$Watchdog = Join-Path $Root 'scripts\watchdog.ps1'

$identity = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $identity.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Se necesita una consola elevada (Ejecutar como administrador)."
}

if ($Uninstall) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Output "Tarea '$TaskName' eliminada. La app en marcha NO se detuvo: usa scripts\service.ps1 stop."
    }
    else {
        Write-Output "La tarea '$TaskName' no existe."
    }
    return
}

if (-not (Test-Path -LiteralPath $Watchdog)) {
    throw "No se encontro '$Watchdog'."
}

$arguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "{0}"' -f $Watchdog
$interval  = 'PT{0}M' -f $WatchdogIntervalMinutes

# Se registra por XML y no con New-ScheduledTaskTrigger porque la repeticion
# indefinida (sin Duration) no se puede expresar de forma fiable con el cmdlet
# en PowerShell 5.1.
$xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.3" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Mantiene encendida la webapp DEBUGBI0: arranca en el boot y la relanza si se cae.</Description>
    <URI>\$TaskName</URI>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
      <Delay>PT1M</Delay>
    </BootTrigger>
    <TimeTrigger>
      <Repetition>
        <Interval>$interval</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>2026-01-01T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>$arguments</Arguments>
      <WorkingDirectory>$Root</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Output "La tarea '$TaskName' ya existe; se reemplaza."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask -TaskName $TaskName -Xml $xml -Force | Out-Null

Write-Output "Tarea '$TaskName' registrada."
Write-Output "  Accion:    powershell.exe $arguments"
Write-Output "  Usuario:   SYSTEM (sin contrasena, arranca sin sesion iniciada)"
Write-Output "  Triggers:  arranque del sistema (+1 min) y cada $WatchdogIntervalMinutes min"
Write-Output ""
Write-Output "Arrancala ahora con:  scripts\service.ps1 start"
