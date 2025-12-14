from __future__ import annotations

import datetime as dt
import logging
import secrets as secrets_lib
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.security import create_admin_jwt, hash_password, require_admin, verify_password
from app.core.config import settings
from app.core.ratelimit import limiter
from app.db.models import AdminUser, AppSetting, PromoCode
from app.db.session import get_db

logger = logging.getLogger(__name__)

def require_admin_route_secret(request: Request) -> None:
    """
    Дополнительная защита "скрытой" админки.

    Если ADMIN_ROUTE_SECRET задан:
    - все запросы к /api/admin/* должны содержать заголовок X-Admin-Route-Secret
    - значение сравниваем через compare_digest (защита от timing attacks)
    
    ВАЖНО: 
    - не читаем body здесь, только проверяем заголовки.
    - пропускаем OPTIONS запросы (preflight для CORS).
    """
    # Пропускаем OPTIONS запросы для CORS preflight
    if request.method == "OPTIONS":
        return
    
    if not settings.admin_route_secret:
        return

    provided = request.headers.get("X-Admin-Route-Secret", "")
    expected = settings.admin_route_secret
    if not secrets_lib.compare_digest(str(provided), str(expected)):
        raise HTTPException(status_code=404, detail="Не найдено.")

class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class MeResponse(BaseModel):
    username: str


class SettingsPayload(BaseModel):
    """
    Набор настроек для админки.
    
    ВАЖНО:
    - Это "тонкая настройка". Храним в БД как key/value.
    - Если каких-то значений нет, фронтенд может показать дефолты.
    """

    telegram_enabled: bool = True
    telegram_chat_id: str = ""
    telegram_template_win: str = "🎉 Победа! Ваш промокод: {code}\nСпасибо за игру! Делитесь удачей с друзьями."
    telegram_template_lose: str = "😔 Сегодня не повезло, но вы молодец!\nПопробуйте ещё раз, удача любит настойчивых."

    promo_ttl_hours: int = 72
    promo_daily_limit: int = 500

    default_difficulty: str = "medium"

    # Тема как JSON-строка (позже можно сделать объектом). Пока минимально.
    theme_json: str = ""

class ChangePasswordRequest(BaseModel):
    """
    Запрос на смену пароля администратора.

    ВАЖНО:
    - Пароль не логируем.
    - Минимальная политика: длина >= 12.
    """

    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)


class PromoItem(BaseModel):
    code: str
    created_at: str
    expires_at: str
    status: str


router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    # ВАЖНО: применяем к каждому эндпоинту админки (включая /login).
    dependencies=[Depends(require_admin_route_secret)],
)

# ВАЖНО: Пересобираем модели Pydantic ПОСЛЕ определения роутера, но ДО определения функций
# (необходимо из-за использования `from __future__ import annotations`)
# Это нужно для корректной работы FastAPI с forward references
LoginRequest.model_rebuild()
MeResponse.model_rebuild()
SettingsPayload.model_rebuild()
ChangePasswordRequest.model_rebuild()
PromoItem.model_rebuild()


def _upsert_setting(db: Session, key: str, value: str) -> None:
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row:
        row.value = value
    else:
        db.add(AppSetting(key=key, value=value))


def _get_setting(db: Session, key: str, default: str) -> str:
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    return row.value if row else default


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request, 
    response: Response, 
    db: Session = Depends(get_db)
) -> dict[str, str]:
    """
    Логин админки.
    Возвращаем ok=true и ставим HttpOnly-cookie с JWT.
    
    ВАЖНО: 
    - Используем ручной парсинг body для обхода проблемы с forward references при использовании `from __future__ import annotations`.
    - Это необходимо, потому что FastAPI создает TypeAdapter при парсинге декоратора, и model_rebuild() не помогает.
    """
    import json
    from pydantic import ValidationError
    
    body = await request.body()
    try:
        data = json.loads(body)
        payload = LoginRequest(**data)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Ошибка парсинга JSON: {str(e)}")
    except ValidationError as e:
        # Форматируем ошибки валидации Pydantic
        errors = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append(f"{field}: {error['msg']}")
        raise HTTPException(status_code=422, detail=", ".join(errors))
    
    admin: AdminUser | None = db.query(AdminUser).filter(AdminUser.username == payload.username).first()
    if not admin or admin.disabled or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль.")

    token = create_admin_jwt(admin.username, expires_hours=12)

    # ВАЖНО:
    # - HttpOnly: JS не может прочитать cookie -> меньше XSS риска.
    # - SameSite=Lax: достаточно для большинства сценариев, и безопаснее чем None.
    # - Secure=True будем включать в продакшене за Nginx/HTTPS.
    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.app_env != "dev",
        max_age=12 * 60 * 60,
    )
    return {"ok": "true"}


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie("admin_token")
    return {"ok": "true"}


@router.get("/me", response_model=MeResponse)
def me(admin: AdminUser = Depends(require_admin)) -> MeResponse:
    return MeResponse(username=admin.username)


@router.get("/settings", response_model=SettingsPayload)
def get_settings(
    admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)
) -> SettingsPayload:
    _ = admin
    # Читаем telegram_chat_id из БД, если нет - из .env (как в app_settings.py)
    telegram_chat_id_db = _get_setting(db, "telegram_chat_id", "")
    telegram_chat_id = telegram_chat_id_db if telegram_chat_id_db else settings.telegram_chat_id

    # Миграция старых шаблонов (если в БД сохранены старые значения)
    legacy_win = "Победа! Промокод выдан: {code}"
    legacy_lose = "Проигрыш"
    new_win = "🎉 Победа! Ваш промокод: {code}\nСпасибо за игру! Делитесь удачей с друзьями."
    new_lose = "😔 Сегодня не повезло, но вы молодец!\nПопробуйте ещё раз, удача любит настойчивых."

    win_raw = _get_setting(db, "telegram_template_win", new_win)
    lose_raw = _get_setting(db, "telegram_template_lose", new_lose)

    migrated = False
    if win_raw == legacy_win:
        win_raw = new_win
        _upsert_setting(db, "telegram_template_win", new_win)
        migrated = True
    if lose_raw == legacy_lose:
        lose_raw = new_lose
        _upsert_setting(db, "telegram_template_lose", new_lose)
        migrated = migrated or lose_raw == new_lose
    if migrated:
        db.commit()

    return SettingsPayload(
        telegram_enabled=_get_setting(db, "telegram_enabled", "true").lower() in {"1", "true", "yes", "on"},
        telegram_chat_id=telegram_chat_id,
        telegram_template_win=win_raw,
        telegram_template_lose=lose_raw,
        promo_ttl_hours=int(_get_setting(db, "promo_ttl_hours", "72") or "72"),
        promo_daily_limit=int(_get_setting(db, "promo_daily_limit", "500") or "500"),
        default_difficulty=_get_setting(db, "default_difficulty", "medium"),
        theme_json=_get_setting(db, "theme_json", ""),
    )


@router.put("/settings")
def put_settings(
    payload: SettingsPayload, admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)
) -> dict[str, str]:
    """
    Сохранение настроек админки.
    
    ВАЖНО:
    - Все настройки сохраняются в БД.
    - Логируем успешное сохранение для отладки.
    """
    _ = admin

    try:
        logger.info(
            "Сохранение настроек админки",
            extra={
                "admin": admin.username,
                "telegram_enabled": payload.telegram_enabled,
                "telegram_chat_id": payload.telegram_chat_id[:10] + "..." if len(payload.telegram_chat_id) > 10 else payload.telegram_chat_id,
            }
        )

        _upsert_setting(db, "telegram_enabled", "true" if payload.telegram_enabled else "false")
        _upsert_setting(db, "telegram_chat_id", payload.telegram_chat_id)
        _upsert_setting(db, "telegram_template_win", payload.telegram_template_win)
        _upsert_setting(db, "telegram_template_lose", payload.telegram_template_lose)

        _upsert_setting(db, "promo_ttl_hours", str(payload.promo_ttl_hours))
        _upsert_setting(db, "promo_daily_limit", str(payload.promo_daily_limit))

        _upsert_setting(db, "default_difficulty", payload.default_difficulty)
        _upsert_setting(db, "theme_json", payload.theme_json)

        db.commit()
        
        logger.info("Настройки успешно сохранены", extra={"admin": admin.username})
        return {"ok": "true"}
    except Exception as e:
        logger.error(
            "Ошибка при сохранении настроек",
            extra={"admin": admin.username, "error": str(e)},
            exc_info=True
        )
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении настроек: {str(e)}")

@router.post("/change-password")
@limiter.limit("5/minute")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    admin: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Смена пароля администратора.

    ВАЖНО:
    - Требуем текущий пароль.
    - После смены перевыдаём JWT cookie.
    """
    if not verify_password(payload.current_password, admin.password_hash):
        raise HTTPException(status_code=400, detail="Текущий пароль указан неверно.")

    admin.password_hash = hash_password(payload.new_password)
    db.commit()

    token = create_admin_jwt(admin.username, expires_hours=12)
    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.app_env != "dev",
        max_age=12 * 60 * 60,
    )
    return {"ok": "true"}




@router.get("/promos")
def list_promos(
    limit: int = 50, admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)
) -> dict[str, Any]:
    _ = admin

    limit = max(1, min(limit, 500))
    stmt = select(PromoCode).order_by(desc(PromoCode.created_at)).limit(limit)
    rows = db.scalars(stmt).all()
    return {
        "items": [
            PromoItem(
                code=r.code,
                created_at=r.created_at.isoformat() if isinstance(r.created_at, dt.datetime) else str(r.created_at),
                expires_at=r.expires_at.isoformat() if isinstance(r.expires_at, dt.datetime) else str(r.expires_at),
                status=r.status.value,
            ).model_dump()
            for r in rows
        ]
    }


