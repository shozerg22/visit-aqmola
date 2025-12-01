# План тестирования и деплоя

## Тестирование

- Юнит/интеграционные: pytest + pytest-asyncio; быстрый прогон без БД (`DISABLE_DB_INIT=1`).
- Покрытие: `pytest --cov=. --cov-report=xml` (артефакт coverage.xml в CI).
- Эндпоинты: health, AI stub/openai, интеграции (заглушки), жалобы/события, RAG (ингест/поиск).
- Следующие шаги:
  - Добавить e2e-тесты CRUD с реальной БД (Docker Postgres) и миграциями Alembic.
  - Нагрузочные (k6/Locust) на ключевые маршруты (/objects, /ai/chat, /rag/search).
  - Безопасность: заголовки, лимиты, проверка админ-эндпоинтов.

## CI/CD

- CI (GitHub Actions):
  - Установка зависимостей, тесты с `DISABLE_DB_INIT=1`, отчёт покрытия как артефакт.
  - Расширение: матрица Python версий, job с Docker Postgres для БД-тестов.
- CD (варианты):
  - Docker образ (GitHub Container Registry), деплой в VM/Kubernetes.
  - Конфиги: `DATABASE_URL`, `ADMIN_TOKEN`, `AI_PROVIDER`, `OPENAI_*`, `AI_USE_RAG`, `RAG_DATA_DIR`.

## Локальный запуск

```powershell
# Без БД (быстрый старт)
.\scripts\run.ps1 -NoDb

# С БД (Docker Desktop требуется)
.\scripts\up.ps1
```

## Импорт/экспорт API

```powershell
# Экспорт OpenAPI
.\scripts\export-openapi.ps1
```

## RAG: быстрый тест

1) Добавить документ:
```bash
curl -X POST "http://localhost:8000/api/v1/rag/documents" \
  -H "Content-Type: application/json" \
  -d '{"title":"Burabay Guide","text":"Burabay National Park...","lang":"EN"}'
```

2) Поиск:
```bash
curl "http://localhost:8000/api/v1/rag/search?q=Burabay+lakes"
```
