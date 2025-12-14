from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import AppSetting


def get_setting(db: Session, key: str) -> str | None:
    """
    Получить значение настройки из БД.
    Возвращает None, если ключа нет.
    """
    stmt = select(AppSetting).where(AppSetting.key == key)
    row = db.scalars(stmt).first()
    return row.value if row else None


def get_bool_setting(db: Session, key: str, default: bool) -> bool:
    """
    Утилита: читает bool настройку (true/false/1/0).
    """
    raw = get_setting(db, key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def telegram_enabled(db: Session) -> bool:
    """
    Telegram можно выключить через БД-настройку, но также есть дефолт из .env.
    """
    return get_bool_setting(db, "telegram_enabled", settings.telegram_enabled)


def telegram_chat_id(db: Session) -> str:
    """
    chat_id можно хранить в БД (настройка), иначе берём из .env.
    """
    return get_setting(db, "telegram_chat_id") or settings.telegram_chat_id


def telegram_template_win(db: Session) -> str:
    """
    Шаблон сообщения о победе.
    """
    return get_setting(db, "telegram_template_win") or "Победа! Промокод выдан: {code}"


def telegram_template_lose(db: Session) -> str:
    """
    Шаблон сообщения о проигрыше.
    """
    return get_setting(db, "telegram_template_lose") or "Проигрыш"


def promo_ttl_hours(db: Session) -> int:
    """
    TTL промокода (в часах). Можно менять из админки.
    """
    raw = get_setting(db, "promo_ttl_hours")
    if raw is None:
        return settings.promo_ttl_hours
    try:
        return int(raw)
    except ValueError:
        return settings.promo_ttl_hours


def promo_daily_limit(db: Session) -> int:
    """
    Дневной лимит выдач (0 = без лимита).
    """
    raw = get_setting(db, "promo_daily_limit")
    if raw is None:
        return settings.promo_daily_limit
    try:
        return int(raw)
    except ValueError:
        return settings.promo_daily_limit


def default_difficulty(db: Session) -> str:
    """
    Сложность по умолчанию для новых игр.
    """
    return get_setting(db, "default_difficulty") or "medium"


