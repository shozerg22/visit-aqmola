Param(
  [switch]$Install
)
# Simple build wrapper for Windows PowerShell
Write-Host "[VisitAqmola Web] Starting build" -ForegroundColor Cyan
if ($Install -or -not (Test-Path node_modules)) {
  Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
  npm install
}
Write-Host "Running build:web..." -ForegroundColor Yellow
npm run build:web
Write-Host "Build finished. Open dist/index.html" -ForegroundColor Green
