"""init

Revision ID: 0001_init
Revises:
Create Date: 2025-12-13

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Первая миграция: создаём таблицы.

    ВАЖНО:
    - Используем UUID/JSONB и timezone-aware timestamps.
    - Это соответствует Postgres (production).
    """
    # Типы Postgres
    from sqlalchemy.dialects import postgresql

    # game_sessions
    op.create_table(
        "game_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        # Строковые значения должны совпадать с app.db.models.GameStatus (value).
        sa.Column("status", sa.Enum("IN_PROGRESS", "WIN", "LOSE", "DRAW", name="gamestatus"), nullable=False),
        sa.Column("difficulty", sa.Enum("easy", "medium", "hard", name="botdifficulty"), nullable=False),
        sa.Column("board", sa.String(length=9), nullable=False, server_default=sa.text("'.........'")),
        sa.Column("history", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tg_win_sent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("tg_lose_sent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    # admin_users
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("disabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_unique_constraint("uq_admin_users_username", "admin_users", ["username"])

    # app_settings
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    )
    op.create_unique_constraint("uq_app_settings_key", "app_settings", ["key"])

    # promo_codes
    op.create_table(
        "promo_codes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=5), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        # Строковые значения должны совпадать с app.db.models.PromoStatus (value).
        sa.Column("status", sa.Enum("ISSUED", "REDEEMED", "EXPIRED", name="promostatus"), nullable=False),
        sa.Column("game_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["game_session_id"], ["game_sessions.id"], name="fk_promo_codes_game_session_id_game_sessions"),
    )
    op.create_unique_constraint("uq_promo_codes_code", "promo_codes", ["code"])


def downgrade() -> None:
    # Удаляем таблицы в обратном порядке зависимостей.
    op.drop_table("promo_codes")
    op.drop_table("app_settings")
    op.drop_table("admin_users")
    op.drop_table("game_sessions")

    # Удаляем enum-типы (Postgres).
    op.execute("DROP TYPE IF EXISTS promostatus")
    op.execute("DROP TYPE IF EXISTS botdifficulty")
    op.execute("DROP TYPE IF EXISTS gamestatus")


