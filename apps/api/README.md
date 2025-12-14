## Backend (FastAPI)

Бекенд является источником истины для игры: он принимает ходы игрока, делает ход компьютера, определяет победу/поражение, выдаёт промокоды и отправляет уведомления в Telegram.

### Переменные окружения
См. корневой файл `.env.example`.

### Локальный запуск (Windows 11, `.venv`)
Подробная инструкция: `docs/development_windows_venv.md`.

Коротко:
1) Создать `.venv` в корне проекта и установить зависимости из `apps/api/requirements*.txt`.
2) Поднять Postgres (рекомендуется: `docker compose -f infra/docker-compose.yml up -d db`).
3) Применить миграции: `alembic upgrade head`.
4) Запустить: `uvicorn app.main:app --reload --port 8000`.

### Миграции (Alembic)
- Конфиг: `apps/api/alembic.ini`
- Среда: `apps/api/alembic/env.py`
- Первая миграция: `apps/api/alembic/versions/0001_init.py`



