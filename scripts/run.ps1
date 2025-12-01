Param(
    [switch]$NoDb
)

$env:PYTHONUNBUFFERED='1'
if ($NoDb) { $env:DISABLE_DB_INIT='1' }

uvicorn app:app --reload --host 0.0.0.0 --port 8000
