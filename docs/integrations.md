# Интеграции VisitAqmola

## eGov Mobile (OIDC)
- Поток: Authorization Code Flow (PKCE при необходимости)
- Redirect URI: `https://visit.aqmola.kz/auth/callback`
- Скоупы: минимально необходимые (профиль пользователя)
- Обмен кода: бэкенд `/api/v1/auth/oidc/verify`
- Результат: создание/привязка пользователя по `external_id`

## eGov Pay / Kaspi QR
- Вебхук платежей: `POST /api/v1/payments/webhook`
- Подпись/секрет: хранить в конфиге, проверка HMAC
- Статусы: `pending`, `paid`, `failed`, `refunded`

## Freedom Travel
- Каталог туров/бронирования (sandbox → prod)
- Временная заглушка: `GET /api/v1/freedom/mock/tours`

## Booking.com / TripAdvisor
- Партнёрские API: запрос доступа
- Использование: рекомендации/рейтинг/наличие

## DataHub
- Импорт метаданных объектов, событий, загруженности
- Периодическая синхронизация (cron / webhook)
