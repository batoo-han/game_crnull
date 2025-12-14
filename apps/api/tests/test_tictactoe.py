from app.services import tictactoe


def test_evaluate_wins_rows() -> None:
    # X выигрывает по верхней строке
    board = "XXX......"
    res = tictactoe.evaluate(board)
    assert res.winner == tictactoe.PLAYER_X
    assert res.is_draw is False


def test_evaluate_draw() -> None:
    # Ничья без пустых клеток и без победителя
    board = "XOXOOXXXO"
    res = tictactoe.evaluate(board)
    assert res.winner is None
    assert res.is_draw is True


def test_hard_blocks_immediate_win() -> None:
    # Игрок (X) собирается выиграть, боту надо блокировать.
    # X X .
    # . O .
    # . . .
    board = "XX..O...."
    move = tictactoe.choose_move_hard(board)
    assert move == 2


