from __future__ import annotations

import datetime as dt
import secrets

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import GameSession, PromoCode


def _today_utc_start() -> dt.datetime:
    """
    Начало текущих суток в UTC.
    """
    now = dt.datetime.utcnow()
    return dt.datetime(year=now.year, month=now.month, day=now.day)


def issued_today_count(db: Session) -> int:
    """
    Считает, сколько промокодов выдано сегодня (UTC).

    ВАЖНО:
    - Это используется для дневного лимита.
    - В коммерческом проекте можно заменить на более строгую модель лимитов,
      но для нашей нагрузки этого достаточно.
    """
    start = _today_utc_start()
    stmt = select(func.count()).select_from(PromoCode).where(PromoCode.created_at >= start)
    return int(db.execute(stmt).scalar_one())


def generate_5digit_code() -> str:
    """
    Генерирует 5-значный код (цифры).

    ВАЖНО:
    - Используем secrets (криптостойкий генератор), а не random.
    """
    n = secrets.randbelow(100_000)
    return f"{n:05d}"


def issue_promo_for_session(db: Session, session: GameSession) -> PromoCode:
    """
    Выдаёт промокод для конкретной игровой сессии.

    Гарантии:
    - для одной сессии выдаём максимум один промокод
    - соблюдаем дневной лимит (если включён)
    - защищаемся от коллизий уникального ограничения в БД
    """
    if session.promo_code is not None:
        return session.promo_code

    # Дневной лимит (0 = без лимита) — берём из админских настроек (БД) или .env.
    from app.services.app_settings import promo_daily_limit, promo_ttl_hours

    daily_limit = promo_daily_limit(db)
    if daily_limit > 0:
        if issued_today_count(db) >= daily_limit:
            # В бизнесе это можно отобразить как “коды закончились”.
            # Но по требованиям проекта промокод должен выдаваться при победе,
            # поэтому мы явно сигналим об ошибке.
            raise RuntimeError("Достигнут дневной лимит выдачи промокодов.")

    expires_at = dt.datetime.utcnow() + dt.timedelta(hours=promo_ttl_hours(db))

    # Повторов 5-значного пространства может быть много, поэтому делаем retry.
    # Опираемся на уникальный индекс в БД.
    last_error: Exception | None = None
    for _ in range(30):
        code = generate_5digit_code()
        promo = PromoCode(code=code, expires_at=expires_at, game_session=session)
        db.add(promo)
        try:
            db.commit()
            db.refresh(promo)
            return promo
        except IntegrityError as e:
            db.rollback()
            last_error = e
            continue

    raise RuntimeError("Не удалось сгенерировать уникальный промокод.") from last_error


def create_promo_code(db: Session) -> PromoCode:
    """
    Создаёт промокод без привязки к игровой сессии (для выигрыша по подаркам).
    
    Использует ту же логику, что и issue_promo_for_session, но без привязки к сессии.
    """
    from app.services.app_settings import promo_daily_limit, promo_ttl_hours

    daily_limit = promo_daily_limit(db)
    if daily_limit > 0:
        if issued_today_count(db) >= daily_limit:
            raise RuntimeError("Достигнут дневной лимит выдачи промокодов.")

    expires_at = dt.datetime.utcnow() + dt.timedelta(hours=promo_ttl_hours(db))

    # Повторов 5-значного пространства может быть много, поэтому делаем retry.
    last_error: Exception | None = None
    for _ in range(30):
        code = generate_5digit_code()
        promo = PromoCode(code=code, expires_at=expires_at, game_session=None)
        db.add(promo)
        try:
            db.commit()
            db.refresh(promo)
            return promo
        except IntegrityError as e:
            db.rollback()
            last_error = e
            continue

    raise RuntimeError("Не удалось сгенерировать уникальный промокод.") from last_error


