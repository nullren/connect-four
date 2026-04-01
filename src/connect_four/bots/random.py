"""A bot that picks a random valid column."""

from __future__ import annotations

import random as _random
from collections.abc import Sequence

from connect_four.engine import build_board, ROWS, COLS


def _valid_moves(moves: Sequence[int]) -> list[int]:
    board = build_board(moves)
    return [c for c in range(COLS) if board[ROWS - 1][c] == 0]


class RandomBot:
    """Picks uniformly at random from valid columns."""

    def next_move(self, moves: Sequence[int]) -> int:
        valid = _valid_moves(moves)
        return _random.choice(valid)
