# Visit Aqmola

Туристический портал Акмолинской области Казахстана с AI-ассистентом.




- Python 3.11+
- OpenRouter API ключ (бесплатный) - [получить здесь](https://openrouter.ai/settings/keys)

### Установка

```bash
# Клонирование
git clone https://github.com/shozerg22/visit-aqmola.git
cd visit-aqmola

# Установка зависимостей
pip install -r requirements.txt

# Настройка .env файла
cp .env.example .env
# Отредактируйте .env и добавьте OPENROUTER_API_KEY
```

### Запуск

```bash
# Windows PowerShell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Или в фоновом режиме
Start-Job -ScriptBlock {
    Set-Location 'путь\к\проекту'
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
}
```

 Запуск

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
