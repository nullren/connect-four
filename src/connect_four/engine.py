"""Pure Connect Four game engine — no external dependencies."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

ROWS: int = 6
COLS: int = 7
WIN_LENGTH: int = 4
MAX_MOVES: int = ROWS * COLS


# ---------------------------------------------------------------------------
# MoveResult — discriminated union
# ---------------------------------------------------------------------------


class MoveResult:
    """Base class for move results. Use pattern matching on the subclasses."""

    @dataclass(frozen=True, slots=True)
    class Ongoing:
        """Game continues; *player* moves next."""

        player: int

    @dataclass(frozen=True, slots=True)
    class Win:
        """Game over — *player* won. *cells* holds the winning coordinates."""

        player: int
        cells: list[tuple[int, int]]

    @dataclass(frozen=True, slots=True)
    class Draw:
        """Game over — board full, no winner."""

    @dataclass(frozen=True, slots=True)
    class InvalidMove:
        """Move was rejected. *reason* explains why."""

        reason: str


# ---------------------------------------------------------------------------
# Standalone utility
# ---------------------------------------------------------------------------


def build_board(moves: Sequence[int]) -> list[list[int]]:
    """Derive a 6×7 board grid from a move sequence.

    Returns a list of *ROWS* lists (row 0 = bottom).  Cell values are
    0 (empty), 1 (player 1), or 2 (player 2).
    """
    board: list[list[int]] = [[0] * COLS for _ in range(ROWS)]
    col_heights = [0] * COLS
    for turn, col in enumerate(moves):
        player = (turn % 2) + 1
        row = col_heights[col]
        board[row][col] = player
        col_heights[col] += 1
    return board


# ---------------------------------------------------------------------------
# Win detection helpers
# ---------------------------------------------------------------------------

# Direction vectors: (delta_row, delta_col)
_DIRECTIONS: list[tuple[int, int]] = [
    (0, 1),   # horizontal →
    (1, 0),   # vertical ↑
    (1, 1),   # diagonal /
    (1, -1),  # diagonal \
]


def _check_win(
    board: list[list[int]], row: int, col: int, player: int
) -> list[tuple[int, int]] | None:
    """Check all four directions from *(row, col)* for a line of four.

    Returns the winning cells if found, otherwise *None*.
    """
    for dr, dc in _DIRECTIONS:
        cells: list[tuple[int, int]] = []
        # Scan in the negative direction first, then positive.
        for sign in (-1, 1):
            r, c = row, col
            if sign == 1:
                # Skip the origin — already counted from the negative pass.
                r, c = row + dr, col + dc
            else:
                pass  # start at origin
            while (
                0 <= r < ROWS
                and 0 <= c < COLS
                and board[r][c] == player
            ):
                if sign == -1:
                    cells.insert(0, (r, c))
                else:
                    cells.append((r, c))
                r += sign * dr
                c += sign * dc
        if len(cells) >= WIN_LENGTH:
            return cells[:WIN_LENGTH]
    return None


# ---------------------------------------------------------------------------
# ConnectFour — the game engine
# ---------------------------------------------------------------------------


class ConnectFour:
    """Full game state, driven by an internal move history."""

    def __init__(self) -> None:
        self._moves: list[int] = []
        self._winner: int | None = None
        self._winning_cells: list[tuple[int, int]] | None = None

    # -- public API ---------------------------------------------------------

    def play(self, col: int) -> MoveResult.Ongoing | MoveResult.Win | MoveResult.Draw | MoveResult.InvalidMove:
        """Play *col* (0-based). Returns a :class:`MoveResult` variant."""
        # Already over?
        if self.is_over:
            return MoveResult.InvalidMove(reason="game is already over")

        # Range check.
        if not (0 <= col < COLS):
            return MoveResult.InvalidMove(reason=f"column {col} is out of range")

        # Column full?
        board = self.board
        if board[ROWS - 1][col] != 0:
            return MoveResult.InvalidMove(reason=f"column {col} is full")

        # Place the token.
        player = self.current_player
        self._moves.append(col)

        # Find where it landed.
        new_board = self.board
        # The row is the topmost occupied cell in this column.
        row = -1
        for r in range(ROWS - 1, -1, -1):
            if new_board[r][col] != 0:
                row = r
                break

        # Win?
        win_cells = _check_win(new_board, row, col, player)
        if win_cells is not None:
            self._winner = player
            self._winning_cells = win_cells
            return MoveResult.Win(player=player, cells=win_cells)

        # Draw?
        if len(self._moves) == MAX_MOVES:
            return MoveResult.Draw()

        # Ongoing.
        return MoveResult.Ongoing(player=self.current_player)

    def undo(self) -> None:
        """Pop the last move. Raises :class:`IndexError` if no moves."""
        if not self._moves:
            raise IndexError("no moves to undo")
        self._moves.pop()
        # Reset cached win state — recompute lazily if needed.
        self._winner = None
        self._winning_cells = None

    # -- properties ---------------------------------------------------------

    @property
    def moves(self) -> Sequence[int]:
        """Read-only view of the move history."""
        return tuple(self._moves)

    @property
    def board(self) -> list[list[int]]:
        """Derived 6×7 grid (row 0 = bottom). Values: 0, 1, 2."""
        return build_board(self._moves)

    @property
    def current_player(self) -> int:
        """Player whose turn it is: 1 or 2."""
        return (len(self._moves) % 2) + 1

    @property
    def valid_moves(self) -> list[int]:
        """Columns that can still accept a token. Empty list if game over."""
        if self.is_over:
            return []
        board = self.board
        return [c for c in range(COLS) if board[ROWS - 1][c] == 0]

    @property
    def is_over(self) -> bool:
        """True when the game has ended (win or draw)."""
        return self._winner is not None or len(self._moves) == MAX_MOVES

    @property
    def winner(self) -> int | None:
        """The winning player (1 or 2), or *None*."""
        return self._winner
