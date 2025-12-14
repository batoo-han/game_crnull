from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


engine = create_engine(
    settings.sqlalchemy_database_url(),
    pool_pre_ping=True,
)

# ВАЖНО:
# - autoflush=False: меньше неожиданных flush'ей; flush делаем осознанно.
# - expire_on_commit=False: удобно для возврата объектов после commit.
SessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=False, expire_on_commit=False)


def get_db() -> Session:
    """
    Dependency для FastAPI: отдаёт сессию БД и гарантирует закрытие.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


