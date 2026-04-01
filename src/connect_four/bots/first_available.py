"""A bot that always picks the leftmost valid column."""

from __future__ import annotations

from collections.abc import Sequence

from connect_four.engine import build_board, ROWS, COLS


def _valid_moves(moves: Sequence[int]) -> list[int]:
    board = build_board(moves)
    return [c for c in range(COLS) if board[ROWS - 1][c] == 0]


class FirstAvailableBot:
    """Always picks the leftmost valid column."""

    def next_move(self, moves: Sequence[int]) -> int:
        valid = _valid_moves(moves)
        return valid[0]
