$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$statePath = Join-Path $taskRoot '.local/services.json'
if (-not (Test-Path -LiteralPath $statePath)) { Write-Output 'No hay servicios registrados por start.ps1.'; exit 0 }
$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
foreach ($service in $state.Backend,$state.Frontend) {
    $process = Get-Process -Id $service.Id -ErrorAction SilentlyContinue
    if ($process) {
        $started = $process.StartTime.ToUniversalTime().ToString('o')
        if ($process.Path -ne $service.Path -or $started -ne $service.Started) { throw 'El PID pertenece a otro proceso. No se detuvo.' }
        Stop-Process -Id $process.Id
    }
}
Remove-Item -LiteralPath $statePath
Write-Output 'Servicios locales detenidos.'
