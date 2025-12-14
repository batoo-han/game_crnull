from __future__ import annotations

import datetime as dt
import enum
import uuid

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """
    Базовый класс для SQLAlchemy моделей.
    """


class GameStatus(str, enum.Enum):
    """
    Статус игры.
    """

    in_progress = "IN_PROGRESS"
    win = "WIN"
    lose = "LOSE"
    draw = "DRAW"


class BotDifficulty(str, enum.Enum):
    """
    Уровень сложности бота.
    """

    easy = "easy"
    medium = "medium"
    hard = "hard"


class GameSession(Base):
    """
    Игровая сессия.

    ВАЖНО:
    - Храним поле как строку из 9 символов: 'X', 'O' или '.'.
    - История ходов хранится в JSON: полезно для аудита/отладки.
    """

    __tablename__ = "game_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ВАЖНО:
    # - В Postgres enum хранится как строка.
    # - Мы хотим хранить именно GameStatus.value (например, "IN_PROGRESS"),
    #   а не имя enum-члена ("in_progress"), иначе получится конфликт с миграцией.
    status: Mapped[GameStatus] = mapped_column(
        Enum(
            GameStatus,
            name="gamestatus",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
        default=GameStatus.in_progress,
    )
    difficulty: Mapped[BotDifficulty] = mapped_column(Enum(BotDifficulty), nullable=False, default=BotDifficulty.medium)

    # '.' = пусто
    board: Mapped[str] = mapped_column(String(9), nullable=False, default=".........")

    # Пример истории:
    # [{"player":"X","cell":0,"ts":"..."} , {"player":"O","cell":4,"ts":"..."}]
    # ВАЖНО: default=list, чтобы у каждого объекта был свой список (не общий).
    history: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)

    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Флаги, чтобы не отправлять Telegram-уведомления повторно при ретраях клиента.
    tg_win_sent: Mapped[bool] = mapped_column(nullable=False, default=False)
    tg_lose_sent: Mapped[bool] = mapped_column(nullable=False, default=False)

    promo_code: Mapped["PromoCode | None"] = relationship(back_populates="game_session", uselist=False)


class PromoStatus(str, enum.Enum):
    """
    Статус промокода.
    """

    issued = "ISSUED"
    redeemed = "REDEEMED"
    expired = "EXPIRED"


class PromoCode(Base):
    """
    Промокод, выдаваемый при победе игрока.

    Требования:
    - уникальный (unique constraint)
    - 5-значный (цифры)
    - срок действия (expires_at)
    """

    __tablename__ = "promo_codes"
    __table_args__ = (UniqueConstraint("code", name="uq_promo_codes_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(5), nullable=False)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Аналогично GameStatus: храним PromoStatus.value ("ISSUED" и т.п.).
    status: Mapped[PromoStatus] = mapped_column(
        Enum(
            PromoStatus,
            name="promostatus",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
        default=PromoStatus.issued,
    )

    game_session_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("game_sessions.id"), nullable=True)
    game_session: Mapped[GameSession | None] = relationship(back_populates="promo_code")


class AdminUser(Base):
    """
    Администратор (один или несколько).

    Пароли в открытом виде НЕ храним.
    """

    __tablename__ = "admin_users"
    __table_args__ = (UniqueConstraint("username", name="uq_admin_users_username"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    disabled: Mapped[bool] = mapped_column(nullable=False, default=False)


class AppSetting(Base):
    """
    Параметры приложения, настраиваемые из админки.

    Упрощённая модель key/value. Value храним строкой (JSON-строка допускается).
    Это удобно для “тонкой” настройки без частых миграций.
    """

    __tablename__ = "app_settings"
    __table_args__ = (UniqueConstraint("key", name="uq_app_settings_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


