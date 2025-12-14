from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Централизованные настройки приложения.

    ВАЖНО:
    - Секреты и параметры окружения берём из .env / переменных окружения.
    - Этот класс используется и в Docker, и локально.
    """

    # ВАЖНО:
    # Alembic часто запускают из `apps/api/`, и тогда относительный путь ".env"
    # указывает на `apps/api/.env`, а не на корневой `.env`.
    # Поэтому фиксируем путь к `.env` относительно корня репозитория.
    _REPO_ROOT = Path(__file__).resolve().parents[4]  # .../apps/api/app/core/config.py -> repo root
    model_config = SettingsConfigDict(
        env_file=str(_REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -----------------------------
    # Общие настройки
    # -----------------------------
    app_name: str = "game_crnull"
    app_env: str = "dev"  # dev | prod
    app_base_url: str = "http://localhost"

    # -----------------------------
    # Backend
    # -----------------------------
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = "CHANGE_ME"
    api_cors_origins: str = "http://localhost:5173"

    # -----------------------------
    # База данных
    # -----------------------------
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "tictactoe"
    postgres_user: str = "tictactoe"
    postgres_password: str = "CHANGE_ME"
    database_url: str | None = None

    # -----------------------------
    # Telegram
    # -----------------------------
    telegram_enabled: bool = True
    telegram_bot_token: str = "CHANGE_ME"
    telegram_chat_id: str = "CHANGE_ME"
    telegram_chat_username: str | None = None

    # -----------------------------
    # Админка
    # -----------------------------
    admin_username: str = "admin"
    admin_initial_password: str = "CHANGE_ME"
    # Дополнительная “маскировка” админки:
    # если значение задано, то все запросы к /api/admin/* должны содержать
    # заголовок X-Admin-Route-Secret с этим значением.
    # Это не заменяет логин/пароль, а дополняет его.
    admin_route_secret: str | None = None

    # -----------------------------
    # Промокоды
    # -----------------------------
    promo_ttl_hours: int = 72
    promo_daily_limit: int = 500

    # -----------------------------
    # Логи
    # -----------------------------
    log_level: str = "INFO"
    log_dir: str = "./logs"

    def cors_origins_list(self) -> list[str]:
        """
        Разбираем строку CORS-оригинов.
        Формат: "http://a, http://b"
        """
        origins = [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]

        # В dev делаем поведение более “дружелюбным”, чтобы не ломать старт проекта,
        # если пользователь сменил порт Vite (например, 5174).
        if self.app_env == "dev":
            for o in ("http://localhost:5173", "http://localhost:5174"):
                if o not in origins:
                    origins.append(o)
        return origins

    def sqlalchemy_database_url(self) -> str:
        """
        Возвращает DSN для SQLAlchemy.

        Приоритет:
        1) DATABASE_URL (если задан)
        2) POSTGRES_* параметры
        """
        if self.database_url:
            return self.database_url

        # psycopg3 рекомендован для SQLAlchemy 2.x + PostgreSQL
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()


