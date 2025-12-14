from __future__ import annotations

import datetime as dt

import jwt
from fastapi import Depends, HTTPException, Request, status
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import AdminUser
from app.db.session import get_db


# FastAPI рекомендует PasswordHash.recommended() (см. документацию).
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Хэшируем пароль (Argon2 через pwdlib).
    """
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """
    Проверяем пароль по хэшу.
    """
    return password_hash.verify(password, hashed)


def create_admin_jwt(username: str, *, expires_hours: int = 12) -> str:
    """
    Создаёт JWT для админки.

    ВАЖНО:
    - Храним JWT в HttpOnly-cookie (не в localStorage), чтобы снизить риск XSS.
    """
    now = dt.datetime.utcnow()
    payload = {
        "sub": username,
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(hours=expires_hours)).timestamp()),
        "typ": "admin"
    }
    return jwt.encode(payload, settings.api_secret_key, algorithm="HS256")


def decode_admin_jwt(token: str) -> dict:
    """
    Декодирует JWT и валидирует подпись/exp.
    """
    return jwt.decode(token, settings.api_secret_key, algorithms=["HS256"])


def get_admin_from_request(request: Request, db: Session) -> AdminUser:
    """
    Достаёт админа из cookie.
    """
    token = request.cookies.get("admin_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация.")

    try:
        payload = decode_admin_jwt(token)
        if payload.get("typ") != "admin":
            raise HTTPException(status_code=401, detail="Некорректный токен.")
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Некорректный токен.")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="Некорректный или просроченный токен.") from e

    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not admin or admin.disabled:
        raise HTTPException(status_code=401, detail="Доступ запрещён.")
    return admin


def require_admin(request: Request, db: Session = Depends(get_db)) -> AdminUser:
    """
    Dependency для защищённых админ-эндпоинтов.
    """
    return get_admin_from_request(request, db)


