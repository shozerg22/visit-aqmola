$env:DISABLE_DB_INIT='1'
if (Test-Path ".\.venv\Scripts\Activate.ps1") { & ".\.venv\Scripts\Activate.ps1" }
python .\scripts\export_openapi.py
Write-Host "OpenAPI exported to openapi.json"