$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $taskRoot 'backend'
$frontendDir = Join-Path $taskRoot 'frontend'
$pythonPath = Join-Path $backendDir '.venv/Scripts/python.exe'
$vitePath = Join-Path $frontendDir 'node_modules/vite/bin/vite.js'
$runtimeDir = Join-Path $taskRoot '.local'
$statePath = Join-Path $runtimeDir 'services.json'
if (-not (Test-Path -LiteralPath $pythonPath) -or -not (Test-Path -LiteralPath $vitePath)) {
    throw 'Instala primero las dependencias siguiendo README.md.'
}
if (Test-Path -LiteralPath $statePath) { throw 'Hay una sesion registrada. Usa scripts/stop.ps1 antes de volver a iniciar.' }
foreach ($port in 8000,5173) {
    $probe = [System.Net.Sockets.TcpClient]::new()
    try { $probe.Connect('127.0.0.1', $port); throw "El puerto $port ya esta ocupado." }
    catch [System.Net.Sockets.SocketException] { }
    finally { $probe.Dispose() }
}
New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
if (-not (Test-Path -LiteralPath (Join-Path $backendDir '.env'))) {
    Copy-Item -LiteralPath (Join-Path $taskRoot '.env.example') -Destination (Join-Path $backendDir '.env')
}
Push-Location $backendDir
try {
    & $pythonPath -m app.seed
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo preparar la base de demostracion.' }
} finally { Pop-Location }
$backendProcess = Start-Process -FilePath $pythonPath -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000') -WorkingDirectory $backendDir -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeDir 'backend-out.log') -RedirectStandardError (Join-Path $runtimeDir 'backend-error.log')
$frontendProcess = $null
try {
    $frontendProcess = Start-Process -FilePath (Get-Command node).Source -ArgumentList @(('"' + $vitePath + '"'),'--configLoader','native','--host','127.0.0.1','--port','5173') -WorkingDirectory $frontendDir -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeDir 'frontend-out.log') -RedirectStandardError (Join-Path $runtimeDir 'frontend-error.log')
    @{ Backend = @{ Id=$backendProcess.Id; Started=$backendProcess.StartTime.ToUniversalTime().ToString('o'); Path=$pythonPath }; Frontend = @{ Id=$frontendProcess.Id; Started=$frontendProcess.StartTime.ToUniversalTime().ToString('o'); Path=(Get-Command node).Source } } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $statePath -Encoding UTF8
    $ready = $false
    for ($attempt = 0; $attempt -lt 15; $attempt++) {
        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 2
            $page = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5173' -TimeoutSec 2
            if ($health.status -eq 'ok' -and $page.StatusCode -eq 200) { $ready=$true; break }
        } catch { Start-Sleep -Milliseconds 500 }
    }
    if (-not $ready) { throw 'El inicio no paso las comprobaciones. Revisa .local/*-error.log.' }
    Write-Output 'ROADMAP OGC: http://127.0.0.1:5173'
    Write-Output 'Credenciales ficticias: .local/demo-access.txt'
    Write-Output 'Para detener: ./scripts/stop.ps1'
} catch {
    if ($frontendProcess) { Stop-Process -Id $frontendProcess.Id -ErrorAction SilentlyContinue }
    Stop-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $statePath) { Remove-Item -LiteralPath $statePath }
    throw
}
