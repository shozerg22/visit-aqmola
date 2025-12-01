Param(
    [switch]$Rebuild
)

$ErrorActionPreference = 'Stop'

# Check Docker CLI
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker CLI не найден. Установите и запустите Docker Desktop."
    exit 1
}

# Check Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Error "Docker не запущен. Пожалуйста, запустите Docker Desktop."
    exit 1
}

if ($Rebuild) { docker compose build }

docker compose up -d db redis

Write-Host "Waiting for Postgres to be ready..."
Start-Sleep -Seconds 5

$env:DISABLE_DB_INIT='0'
$env:PYTHONUNBUFFERED='1'
uvicorn app:app --host 0.0.0.0 --port 8000
