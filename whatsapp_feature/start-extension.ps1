param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$featureRoot = $PSScriptRoot
$projectRoot = Split-Path -Parent $featureRoot
$extensionPython = Join-Path $featureRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $extensionPython)) {
    throw 'The isolated extension environment is missing. See whatsapp_feature/README.md.'
}
Push-Location $projectRoot
try {
    & $extensionPython -B -m whatsapp_feature.run_backend --port $Port
    if ($LASTEXITCODE -ne 0) { throw 'Extension backend stopped with an error. Check the output above.' }
} finally {
    Pop-Location
}
