#!/usr/bin/env sh
set -e

# ВАЖНО:
# - В продакшене таблицы должны создаваться миграциями, а не create_all().
# - Поэтому перед запуском API делаем alembic upgrade.

echo "[api] running migrations..."
alembic upgrade head

echo "[api] starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000


