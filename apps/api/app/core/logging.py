from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

from pythonjsonlogger import jsonlogger

from app.core.config import settings


def configure_logging() -> None:
    """
    Настраивает логирование приложения.

    Требования:
    - несколько уровней логирования (DEBUG/INFO/WARNING/ERROR)
    - ротация, суммарный размер логов <= 100MB

    Реализация:
    - один файл app.log
    - maxBytes=10MB, backupCount=9 -> 10 файлов * 10MB = 100MB
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    os.makedirs(settings.log_dir, exist_ok=True)
    logfile = os.path.join(settings.log_dir, "app.log")

    root = logging.getLogger()
    root.setLevel(log_level)

    # Очищаем хендлеры, чтобы при перезапуске в dev не дублировались сообщения.
    root.handlers.clear()

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    file_handler = RotatingFileHandler(
        logfile,
        maxBytes=10 * 1024 * 1024,
        backupCount=9,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Немного “приглушаем” шумные логгеры.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


