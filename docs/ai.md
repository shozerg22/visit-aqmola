# AI-ассистент — прототип

## Подход
- Провайдеры: `stub` (по умолчанию) и `openai`.
- Точки API: `POST /api/v1/ai/chat` — принимает `{ prompt, lang }`.
- Языки: RU/KZ/EN (передавать в `lang`).

## Конфигурация (ENV)
- `AI_PROVIDER=stub|openai`
- `OPENAI_API_KEY=...`
- `OPENAI_MODEL=gpt-4o-mini` (по умолчанию)

Пример `.env`:
```
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

## Fallback
- При отсутствии ключа или ошибке — безопасный ответ заглушки без внешних вызовов.

## Дальше (RAG)
- Выбрать Vector DB (Pinecone/Milvus) и добавить retrieval из DataHub.
- Встроить контекст (объекты, события, маршруты) в промпт.
