"""Minimax bot with alpha-beta pruning."""

from __future__ import annotations

from collections.abc import Sequence

from connect_four.bots import register
from connect_four.engine import COLS, ROWS, Board, ConnectFour

# Try center columns first — dramatically improves alpha-beta pruning.
_COLUMN_ORDER = (3, 2, 4, 1, 5, 0, 6)


def _order_moves(valid: list[int]) -> list[int]:
    return sorted(valid, key=_COLUMN_ORDER.index)


def _score_window(window: list[int], player: int) -> float:
    opponent = 3 - player
    bot = window.count(player)
    opp = window.count(opponent)
    empty = window.count(0)

    if bot == 4:
        return 1000.0
    if opp == 4:
        return -1000.0
    if bot == 3 and empty == 1:
        return 50.0
    if bot == 2 and empty == 2:
        return 5.0
    if opp == 3 and empty == 1:
        return -80.0
    if opp == 2 and empty == 2:
        return -5.0
    return 0.0


def _evaluate(board: Board, player: int) -> float:
    """Heuristic score of a non-terminal position from *player*'s perspective."""
    score = 0.0

    # Center column preference
    center = COLS // 2
    score += sum(1 for r in range(ROWS) if board[r][center] == player) * 3.0

    # Horizontal windows
    for r in range(ROWS):
        for c in range(COLS - 3):
            score += _score_window([board[r][c + i] for i in range(4)], player)

    # Vertical windows
    for c in range(COLS):
        for r in range(ROWS - 3):
            score += _score_window([board[r + i][c] for i in range(4)], player)

    # Diagonal /
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            score += _score_window([board[r + i][c + i] for i in range(4)], player)

    # Diagonal \
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            score += _score_window([board[r - i][c + i] for i in range(4)], player)

    return score


def _minimax(
    game: ConnectFour,
    depth: int,
    alpha: float,
    beta: float,
    maximizing: bool,
    bot_player: int,
    cache: dict[Board, tuple[float, int]],
) -> float:
    """Alpha-beta minimax. Mutates *game* via play/undo — caller must not rely
    on game state during recursion."""
    if game.is_over:
        if game.winner == bot_player:
            return 1000.0 + depth  # win sooner = better
        if game.winner is not None:
            return -1000.0 - depth  # lose later = less bad
        return 0.0  # draw

    if depth == 0:
        return _evaluate(game.board, bot_player)

    board = game.board  # immutable — safe to use as cache key
    cached = cache.get(board)
    if cached is not None and cached[1] >= depth:
        return cached[0]

    ordered = _order_moves(game.valid_moves)

    if maximizing:
        best = -float("inf")
        for col in ordered:
            game.play(col)
            score = _minimax(game, depth - 1, alpha, beta, False, bot_player, cache)
            game.undo()
            best = max(best, score)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
    else:
        best = float("inf")
        for col in ordered:
            game.play(col)
            score = _minimax(game, depth - 1, alpha, beta, True, bot_player, cache)
            game.undo()
            best = min(best, score)
            beta = min(beta, score)
            if beta <= alpha:
                break

    cache[board] = (best, depth)
    return best


class MinimaxBot:
    """Minimax with alpha-beta pruning. Configurable search depth (default 6)."""

    def __init__(self, max_depth: int = 6) -> None:
        self.max_depth = max_depth

    @property
    def name(self) -> str:
        return "minimax"

    @property
    def description(self) -> str:
        return f"Minimax with alpha-beta pruning (depth {self.max_depth})."

    def next_move(self, moves: Sequence[int]) -> int:
        game = ConnectFour.from_moves(moves)
        bot_player = int(game.current_player)
        ordered = _order_moves(game.valid_moves)
        cache: dict[Board, tuple[float, int]] = {}

        best_score = -float("inf")
        best_col = ordered[0]

        for col in ordered:
            game.play(col)
            score = _minimax(
                game,
                self.max_depth - 1,
                -float("inf"),
                float("inf"),
                False,
                bot_player,
                cache,
            )
            game.undo()
            if score > best_score:
                best_score = score
                best_col = col

        return best_col


register(MinimaxBot())
