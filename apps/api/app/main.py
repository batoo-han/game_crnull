from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import PlainTextResponse

from app.api.game import router as game_router
from app.api.admin import router as admin_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.ratelimit import limiter
from app.db.models import Base
from app.db.session import SessionLocal, engine
from app.services.admin_init import ensure_initial_admin


def create_app() -> FastAPI:
    """
    Фабрика приложения.

    ВАЖНО:
    - Делаем фабрику, чтобы было проще тестировать и запускать разные конфиги.
    """
    configure_logging()
    app = FastAPI(title=settings.app_name)

    # Rate limit (в первую очередь для админ-логина).
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, lambda _r, _e: PlainTextResponse("Слишком много запросов.", status_code=429))
    app.add_middleware(SlowAPIMiddleware)

    # CORS нужен для локальной разработки (web:5173 -> api:8000).
    # В продакшене список должен быть строго ограничен вашим доменом.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(game_router)
    app.include_router(admin_router)

    @app.get("/api/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok"}

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """
        Минимальный request logging middleware.

        ВАЖНО:
        - не логируем тело запросов, чтобы случайно не записать секреты
        - оставляем только метод/путь/код ответа и время
        """
        import time
        import logging

        logger = logging.getLogger("request")
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "http_request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
            },
        )
        return response

    @app.on_event("startup")
    def _startup() -> None:
        """
        В dev-режиме создаём таблицы автоматически, чтобы можно было быстро запуститься.
        В продакшене будем использовать Alembic-миграции.
        """
        if settings.app_env == "dev":
            Base.metadata.create_all(bind=engine)

        # Инициализируем первичного администратора, если он ещё не создан.
        db = SessionLocal()
        try:
            ensure_initial_admin(db)
        finally:
            db.close()

    return app


app = create_app()


