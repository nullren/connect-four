"""A bot that always picks the leftmost valid column."""

from __future__ import annotations

from collections.abc import Sequence

from connect_four.bots import register
from connect_four.engine import build_board, ROWS, COLS


def _valid_moves(moves: Sequence[int]) -> list[int]:
    board = build_board(moves)
    return [c for c in range(COLS) if board[ROWS - 1][c] == 0]


class FirstAvailableBot:
    """Always picks the leftmost valid column."""

    @property
    def name(self) -> str:
        return "first"

    @property
    def description(self) -> str:
        return "Always picks the leftmost valid column."

    def next_move(self, moves: Sequence[int]) -> int:
        return _valid_moves(moves)[0]


register(FirstAvailableBot())
