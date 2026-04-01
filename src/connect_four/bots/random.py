"""A bot that picks a random valid column."""

from __future__ import annotations

import random as _random
from collections.abc import Sequence

from connect_four.bots import register
from connect_four.engine import COLS, ROWS, build_board


def _valid_moves(moves: Sequence[int]) -> list[int]:
    board = build_board(moves)
    return [c for c in range(COLS) if board[ROWS - 1][c] == 0]


class RandomBot:
    """Picks uniformly at random from valid columns."""

    @property
    def name(self) -> str:
        return "random"

    @property
    def description(self) -> str:
        return "Picks uniformly at random from valid columns."

    def next_move(self, moves: Sequence[int]) -> int:
        return _random.choice(_valid_moves(moves))


register(RandomBot())
