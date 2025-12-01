Param(
  [int]$Port = 5173
)

# Простой локальный сервер статики для папки src/web
$ErrorActionPreference = 'Stop'
$root = Join-Path (Join-Path (Join-Path $PSScriptRoot '..') 'src') 'web'
if (-not (Test-Path $root)) { throw "Not found: $root" }

Push-Location $root
try {
  Write-Host "Serving $root at http://localhost:$Port" -ForegroundColor Green
  python -m http.server $Port
} finally {
  Pop-Location
}
