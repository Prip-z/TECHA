# HackBack Backend Scaffold

Чистый каркас для бэка: `FastAPI` + `SQLAlchemy` + `Alembic` + `Postgres` + Docker Compose.

Старые доменные ручки, модели и миграции удалены. В репозитории оставлен только инфраструктурный слой:
- единый конфиг приложения и миграций
- подключение к Postgres
- baseline миграция
- `liveness` и `readiness` ручки
- предсказуемый docker bootstrap

## Что есть сейчас

- `GET /` - краткая информация о сервисе
- `GET /api/health/live` - проверка, что приложение поднялось
- `GET /api/health/ready` - проверка готовности приложения и соединения с Postgres
- `alembic upgrade head` запускается автоматически при старте backend-контейнера

## Быстрый старт

1. При необходимости скопируй `.env.example` в `.env` и поменяй значения.
2. Подними стек:

```bash
docker compose up --build
```

3. Проверь, что всё готово:

```text
http://localhost:8000/api/health/live
http://localhost:8000/api/health/ready
http://localhost:8000/docs
```

## Как подключать фронт

Есть два нормальных сценария.

### Фронт работает в браузере на хосте

Используй API URL:

```text
http://localhost:8000
```

По умолчанию CORS уже разрешен для:
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:5173`
- `http://127.0.0.1:5173`

Плюс по regex разрешены любые `localhost` и `127.0.0.1` с любым портом.

Если у фронта другой origin, добавь его в `CORS_ORIGINS` или поменяй `CORS_ORIGIN_REGEX`.

### Фронт тоже работает в Docker

Этот compose создает общую сеть с фиксированным именем `hackback-app`.

Если фронтовый контейнер сам ходит в backend по внутренней сети Docker, используй адрес:

```text
http://backend:8000
```

Если запросы идут из браузера напрямую, используй `http://localhost:8000`, потому что имя `backend` браузер на хосте не резолвит.

Пример для фронтового `compose.yml`:

```yaml
networks:
  app-net:
    external: true
    name: hackback-app

services:
  frontend:
    build: .
    networks:
      - app-net
```

## Локальный запуск без Docker

1. Подними Postgres любым удобным способом.
2. Установи зависимости:

```bash
python -m pip install -r requirements.txt
```

3. Накати миграции:

```bash
alembic upgrade head
```

4. Запусти приложение:

```bash
uvicorn app.main:app --reload
```

## Переменные окружения

Основные:
- `APP_NAME`
- `APP_ENV`
- `DEBUG`
- `LOG_LEVEL`
- `CORS_ORIGINS`
- `CORS_ORIGIN_REGEX`
- `PG_HOST`
- `PG_PORT`
- `PG_DB`
- `PG_USER`
- `PG_PASS`
- `DB_POOL_SIZE`
- `DB_MAX_OVERFLOW`
- `BACKEND_EXTERNAL_PORT`
- `DB_EXTERNAL_PORT`

Смотри пример в [.env.example](./.env.example).

## Как развивать дальше

- Добавляй модели в `app/model/`
- Импортируй их в `app/model/__init__.py`, чтобы Alembic видел metadata
- После этого делай `alembic revision --autogenerate -m "..."` и `alembic upgrade head`
- Доменные роуты собирай поверх текущего `db/session/config/docker` слоя
