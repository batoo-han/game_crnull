from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.models import AdminUser


def ensure_initial_admin(db: Session) -> None:
    """
    Создаёт первичного администратора, если в БД ещё нет ни одного.

    ВАЖНО:
    - Пароль берём из .env (ADMIN_INITIAL_PASSWORD) только при первичной инициализации.
    - В БД сохраняем только хэш.
    """
    stmt = select(AdminUser)
    exists = db.scalars(stmt).first()
    if exists:
        return

    username = settings.admin_username
    password = settings.admin_initial_password

    admin = AdminUser(username=username, password_hash=hash_password(password), disabled=False)
    db.add(admin)
    db.commit()


