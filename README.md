# Visit Aqmola

Туристический портал Акмолинской области Казахстана.

## Требования

- Docker Desktop (Windows/Mac) или Docker Engine (Linux)
- Docker Compose v2.0+
- Порт 8000 должен быть свободен

## Запуск проекта

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-username/visit-aqmola.git
cd visit-aqmola
```

### 2. Настройка API ключей

Откройте файл `src/web/index.html` и замените API ключи:

Google Maps API (строка 6):
```html
<script async src="https://maps.googleapis.com/maps/api/js?key=ВАШ_КЛЮЧ&callback=console.debug&libraries=maps,marker&v=beta"></script>
```

Google Gemini AI API (строка 169):
```javascript
const GEMINI_API_KEY = 'ВАШ_КЛЮЧ';
```

Получение ключей:
- Google Maps: https://console.cloud.google.com/google/maps-apis
- Gemini AI: https://aistudio.google.com/app/apikey

### 3. Запуск

```bash
docker-compose up --build
```

Для запуска в фоновом режиме:
```bash
docker-compose up -d --build
```

### 4. Открытие сайта

http://localhost:8000

## Остановка проекта

```bash
docker-compose down
```

## Перезапуск

```bash
docker-compose restart
```

## Локальный запуск без Docker

1. Создайте виртуальное окружение:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Запустите сервер:
```bash
uvicorn src.main:app --reload --port 8000
```

## Решение проблем

### Порт 8000 занят

Windows:
```bash
netstat -ano | findstr :8000
```

Linux/Mac:
```bash
lsof -i :8000
```

Или измените порт в docker-compose.yml:
```yaml
ports:
  - "8080:8000"
```

### Docker не запускается

```bash
docker-compose down -v
docker-compose up --build
```
