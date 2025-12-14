from __future__ import annotations

import datetime as dt
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.models import BotDifficulty, GameSession, GameStatus
from app.db.session import get_db
from app.services import tictactoe

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/game", tags=["game"])


class NewGameRequest(BaseModel):
    """
    Запрос на создание новой игры.

    difficulty:
      - easy: случайный бот
      - medium: блокирует/выигрывает при возможности
      - hard: minimax (оптимальный)
    """

    # Если не задано — берём из админских настроек.
    difficulty: BotDifficulty | None = None


class GameStateResponse(BaseModel):
    """
    Ответ с состоянием игры.
    """

    session_id: uuid.UUID
    board: list[str] = Field(min_length=9, max_length=9)
    status: GameStatus
    winner: str | None
    last_player_move: int | None = None
    last_bot_move: int | None = None
    promo_code: str | None = None
    promo_expires_at: str | None = None


class MoveRequest(BaseModel):
    """
    Ход пользователя.
    """

    session_id: uuid.UUID
    cell: int = Field(ge=0, le=8)


@router.post("/new", response_model=GameStateResponse)
def new_game(payload: NewGameRequest, db: Session = Depends(get_db)) -> GameStateResponse:
    """
    Создаёт новую игровую сессию.
    """
    from app.services.app_settings import default_difficulty

    try:
        difficulty = payload.difficulty or BotDifficulty(default_difficulty(db))
    except Exception:
        difficulty = BotDifficulty.medium

    session = GameSession(
        status=GameStatus.in_progress,
        difficulty=difficulty,
        board=tictactoe.EMPTY * 9,
        history=[],
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return GameStateResponse(
        session_id=session.id,
        board=tictactoe.board_to_list(session.board),
        status=session.status,
        winner=None,
    )


@router.post("/move", response_model=GameStateResponse)
def make_move(
    payload: MoveRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> GameStateResponse:
    """
    Применяет ход пользователя и ход компьютера (если игра не закончилась).

    ВАЖНО:
    - Именно сервер решает результат.
    - Клиент не может “сообщить о победе” самостоятельно.
    """
    session: GameSession | None = db.get(GameSession, str(payload.session_id))
    if session is None:
        raise HTTPException(status_code=404, detail="Игровая сессия не найдена.")

    if session.status != GameStatus.in_progress:
        # Если игра закончена, просто возвращаем состояние (клиент может обновиться).
        end_state = tictactoe.evaluate(session.board)
        promo_code = session.promo_code.code if session.promo_code else None
        promo_expires_at = session.promo_code.expires_at.isoformat() if session.promo_code else None
        return GameStateResponse(
            session_id=session.id,
            board=tictactoe.board_to_list(session.board),
            status=session.status,
            winner=end_state.winner,
            promo_code=promo_code,
            promo_expires_at=promo_expires_at,
        )

    # 1) Ход пользователя (X)
    try:
        board_after_player = tictactoe.apply_move(session.board, payload.cell, tictactoe.PLAYER_X)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    session.board = board_after_player
    session.history.append(
        {"player": tictactoe.PLAYER_X, "cell": payload.cell, "ts": dt.datetime.utcnow().isoformat()}
    )

    state = tictactoe.evaluate(session.board)
    if state.winner == tictactoe.PLAYER_X:
        session.status = GameStatus.win
        session.finished_at = dt.datetime.utcnow()
        db.commit()

        # Промокод выдаём только при подтверждённой сервером победе.
        # Реальную отправку в Telegram подключим в следующем todo.
        try:
            from app.services.promo import issue_promo_for_session

            promo = issue_promo_for_session(db, session)
            promo_code = promo.code
            promo_expires_at = promo.expires_at.isoformat()

            # Telegram: сообщение о победе (строго один раз).
            from app.services.app_settings import telegram_chat_id, telegram_enabled, telegram_template_win
            from app.services.telegram import send_telegram_message

            if (not session.tg_win_sent) and telegram_enabled(db):
                chat_id = telegram_chat_id(db)
                logger.info(
                    "Подготовка отправки сообщения о победе в Telegram",
                    extra={
                        "session_id": str(session.id),
                        "chat_id": chat_id[:10] + "..." if len(chat_id) > 10 else chat_id,
                        "promo_code": promo_code,
                    }
                )
                text = telegram_template_win(db).format(code=promo_code)
                # Отправляем в фоне, чтобы не тормозить ответ игроку.
                background_tasks.add_task(send_telegram_message, chat_id=chat_id, text=text)
                session.tg_win_sent = True
                db.commit()
            elif not telegram_enabled(db):
                logger.info("Telegram отключен, сообщение о победе не отправляется", extra={"session_id": str(session.id)})
            elif session.tg_win_sent:
                logger.info("Сообщение о победе уже было отправлено ранее", extra={"session_id": str(session.id)})
        except Exception as e:
            # Если промо не выдался — логируем, чтобы понимать причину (лимит, уникальность и т.п.).
            logger.error(
                "Не удалось выдать промокод при победе",
                extra={"session_id": str(session.id), "error": str(e)},
                exc_info=True,
            )
            promo_code = None
            promo_expires_at = None

        return GameStateResponse(
            session_id=session.id,
            board=tictactoe.board_to_list(session.board),
            status=session.status,
            winner=state.winner,
            last_player_move=payload.cell,
            last_bot_move=None,
            promo_code=promo_code,
            promo_expires_at=promo_expires_at,
        )

    if state.is_draw:
        session.status = GameStatus.draw
        session.finished_at = dt.datetime.utcnow()
        db.commit()
        return GameStateResponse(
            session_id=session.id,
            board=tictactoe.board_to_list(session.board),
            status=session.status,
            winner=None,
            last_player_move=payload.cell,
            last_bot_move=None,
        )

    # 2) Ход компьютера (O)
    bot_move = tictactoe.choose_bot_move(session.board, session.difficulty.value)
    session.board = tictactoe.apply_move(session.board, bot_move, tictactoe.PLAYER_O)
    session.history.append(
        {"player": tictactoe.PLAYER_O, "cell": bot_move, "ts": dt.datetime.utcnow().isoformat()}
    )

    state2 = tictactoe.evaluate(session.board)
    if state2.winner == tictactoe.PLAYER_O:
        session.status = GameStatus.lose
        session.finished_at = dt.datetime.utcnow()
        # Telegram: сообщение о проигрыше (строго один раз).
        try:
            from app.services.app_settings import telegram_chat_id, telegram_enabled, telegram_template_lose
            from app.services.telegram import send_telegram_message

            if (not session.tg_lose_sent) and telegram_enabled(db):
                chat_id = telegram_chat_id(db)
                logger.info(
                    "Подготовка отправки сообщения о проигрыше в Telegram",
                    extra={
                        "session_id": str(session.id),
                        "chat_id": chat_id[:10] + "..." if len(chat_id) > 10 else chat_id,
                    }
                )
                text = telegram_template_lose(db)
                background_tasks.add_task(send_telegram_message, chat_id=chat_id, text=text)
                session.tg_lose_sent = True
            elif not telegram_enabled(db):
                logger.info("Telegram отключен, сообщение о проигрыше не отправляется", extra={"session_id": str(session.id)})
            elif session.tg_lose_sent:
                logger.info("Сообщение о проигрыше уже было отправлено ранее", extra={"session_id": str(session.id)})
        except Exception as e:
            # Ошибка Telegram не должна ломать игровой ответ.
            logger.error(
                "Ошибка при подготовке отправки сообщения о проигрыше",
                extra={"session_id": str(session.id), "error": str(e)},
                exc_info=True
            )
    elif state2.is_draw:
        session.status = GameStatus.draw
        session.finished_at = dt.datetime.utcnow()

    db.commit()

    return GameStateResponse(
        session_id=session.id,
        board=tictactoe.board_to_list(session.board),
        status=session.status,
        winner=state2.winner,
        last_player_move=payload.cell,
        last_bot_move=bot_move,
    )


@router.get("/{session_id}", response_model=GameStateResponse)
def get_game(session_id: uuid.UUID, db: Session = Depends(get_db)) -> GameStateResponse:
    """
    Возвращает текущее состояние игры.
    """
    session: GameSession | None = db.get(GameSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Игровая сессия не найдена.")

    state = tictactoe.evaluate(session.board)
    promo_code = session.promo_code.code if session.promo_code else None
    promo_expires_at = session.promo_code.expires_at.isoformat() if session.promo_code else None
    return GameStateResponse(
        session_id=session.id,
        board=tictactoe.board_to_list(session.board),
        status=session.status,
        winner=state.winner,
        promo_code=promo_code,
        promo_expires_at=promo_expires_at,
    )


class PromoCodeResponse(BaseModel):
    """Ответ с промокодом для выигрыша по подаркам."""

    promo_code: str
    promo_expires_at: str
    message: str


class GiftPromoRequest(BaseModel):
    """
    Запрос на промокод за подарки.

    Желательно передавать session_id, чтобы привязать код к сессии (колонка NOT NULL).
    """

    session_id: uuid.UUID | None = None


@router.post("/gift-promo", response_model=PromoCodeResponse)
def get_gift_promo(
    payload: GiftPromoRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> PromoCodeResponse:
    """
    Выдаёт промокод при выигрыше по подаркам (собрано 3 подарка).
    """
    from app.services.promo import create_promo_code, issue_promo_for_session
    logger.info(
        "Запрос промокода за подарки",
        extra={"session_id": str(payload.session_id) if payload.session_id else None},
    )

    try:
        promo = None
        if payload.session_id:
            session = db.get(GameSession, str(payload.session_id))
            if session is None:
                logger.warning("Сессия для подарков не найдена, fallback на выдачу без привязки")
            else:
                promo = issue_promo_for_session(db, session)
        if promo is None:
            promo = create_promo_code(db)
            logger.warning("Выдача промокода за подарки без session_id (fallback)")

        promo_code = promo.code
        promo_expires_at = promo.expires_at.isoformat()
        message = f"🎁 Победа по подаркам! Ваш промокод: {promo_code}"

        # Telegram: сообщение о победе по подаркам
        from app.services.app_settings import telegram_chat_id, telegram_enabled, telegram_template_win
        from app.services.telegram import send_telegram_message

        if telegram_enabled(db):
            text = telegram_template_win(db).format(code=promo_code)
            background_tasks.add_task(send_telegram_message, chat_id=telegram_chat_id(db), text=text)
            logger.info("Отправка в Telegram промо за подарки", extra={"chat_id": telegram_chat_id(db), "promo_code": promo_code})

        return PromoCodeResponse(promo_code=promo_code, promo_expires_at=promo_expires_at, message=message)
    except Exception as e:
        logger.error("Ошибка выдачи промокода за подарки", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Не удалось выдать промокод: {str(e)}") from e


