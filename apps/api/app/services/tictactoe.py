from __future__ import annotations

import random
from dataclasses import dataclass


PLAYER_X = "X"  # пользователь
PLAYER_O = "O"  # компьютер
EMPTY = "."


WIN_LINES: tuple[tuple[int, int, int], ...] = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


@dataclass(frozen=True)
class GameEval:
    """
    Результат вычисления состояния игры.

    winner:
      - "X" если победил пользователь
      - "O" если победил компьютер
      - None если победителя нет
    """

    winner: str | None
    is_draw: bool


def board_to_list(board: str) -> list[str]:
    """
    Преобразует строку поля в список длины 9.
    """
    return list(board)


def list_to_board(cells: list[str]) -> str:
    """
    Преобразует список длины 9 в строку поля.
    """
    return "".join(cells)


def available_moves(board: str) -> list[int]:
    """
    Возвращает индексы свободных клеток.
    """
    return [i for i, c in enumerate(board) if c == EMPTY]


def evaluate(board: str) -> GameEval:
    """
    Определяет победителя/ничью на текущем поле.
    """
    for a, b, c in WIN_LINES:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return GameEval(winner=board[a], is_draw=False)

    if EMPTY not in board:
        return GameEval(winner=None, is_draw=True)

    return GameEval(winner=None, is_draw=False)


def apply_move(board: str, cell: int, player: str) -> str:
    """
    Применяет ход и возвращает новое поле.
    """
    if cell < 0 or cell > 8:
        raise ValueError("Некорректная клетка. Допустимы значения 0..8.")
    if board[cell] != EMPTY:
        raise ValueError("Клетка уже занята.")
    if player not in (PLAYER_X, PLAYER_O):
        raise ValueError("Некорректный игрок.")

    cells = board_to_list(board)
    cells[cell] = player
    return list_to_board(cells)


def choose_move_easy(board: str) -> int:
    """
    Easy: случайный ход.
    """
    moves = available_moves(board)
    return random.choice(moves)


def _find_winning_move(board: str, player: str) -> int | None:
    """
    Ищет ход, который немедленно приносит победу player.
    """
    for m in available_moves(board):
        b2 = apply_move(board, m, player)
        if evaluate(b2).winner == player:
            return m
    return None


def choose_move_medium(board: str) -> int:
    """
    Medium:
    1) Если можно выиграть сейчас — выиграть.
    2) Если нужно блокировать немедленную победу игрока — блокировать.
    3) Иначе — центр, затем углы, затем случайно.
    """
    win_now = _find_winning_move(board, PLAYER_O)
    if win_now is not None:
        return win_now

    block = _find_winning_move(board, PLAYER_X)
    if block is not None:
        return block

    if board[4] == EMPTY:
        return 4

    corners = [i for i in (0, 2, 6, 8) if board[i] == EMPTY]
    if corners:
        return random.choice(corners)

    return choose_move_easy(board)


def _minimax(board: str, current: str, depth: int) -> tuple[int, int]:
    """
    Minimax для 3×3.

    Возвращает (score, move).
    - score: чем больше, тем лучше для компьютера (O)
    - move: индекс клетки, -1 если ходов нет

    Примечание:
    - depth используется, чтобы предпочитать более быстрые победы и более долгие поражения.
    """
    state = evaluate(board)
    if state.winner == PLAYER_O:
        return (10 - depth, -1)
    if state.winner == PLAYER_X:
        return (-10 + depth, -1)
    if state.is_draw:
        return (0, -1)

    moves = available_moves(board)

    # Максимизируем, если ходит O; минимизируем, если ходит X.
    if current == PLAYER_O:
        best_score = -10_000
        best_move = moves[0]
        for m in moves:
            b2 = apply_move(board, m, PLAYER_O)
            score, _ = _minimax(b2, PLAYER_X, depth + 1)
            if score > best_score:
                best_score = score
                best_move = m
        return (best_score, best_move)
    else:
        best_score = 10_000
        best_move = moves[0]
        for m in moves:
            b2 = apply_move(board, m, PLAYER_X)
            score, _ = _minimax(b2, PLAYER_O, depth + 1)
            if score < best_score:
                best_score = score
                best_move = m
        return (best_score, best_move)


def choose_move_hard(board: str) -> int:
    """
    Hard: оптимальная стратегия (minimax).

    ВАЖНО:
    - Для 3×3 minimax очень быстрый и не создаёт проблем производительности.
    """
    _, move = _minimax(board, PLAYER_O, depth=0)
    if move == -1:
        # Фолбэк: на всякий случай
        return choose_move_easy(board)
    return move


def choose_bot_move(board: str, difficulty: str) -> int:
    """
    Выбирает ход бота согласно уровню сложности.
    """
    if difficulty == "easy":
        return choose_move_easy(board)
    if difficulty == "medium":
        return choose_move_medium(board)
    if difficulty == "hard":
        return choose_move_hard(board)
    # Безопасный дефолт
    return choose_move_medium(board)


