"""Interactive terminal UI for Connect Four."""

from __future__ import annotations

import sys

from connect_four.engine import ConnectFour, MoveResult, ROWS, COLS
from connect_four.players import HumanPlayer, QuitRequested, UndoRequested

_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_RED    = "\033[91m"
_YELLOW = "\033[93m"
_CYAN   = "\033[96m"
_DIM    = "\033[2m"

_cell = "───"
_TOP = "┌" + "┬".join([_cell] * COLS) + "┐"
_SEP = "├" + "┼".join([_cell] * COLS) + "┤"
_BOT = "└" + "┴".join([_cell] * COLS) + "┘"


def render_board(
    board: list[list[int]],
    highlight: set[tuple[int, int]] | None = None,
) -> str:
    """Render the board using Unicode box-drawing characters."""
    if highlight is None:
        highlight = set()

    lines: list[str] = []
    lines.append("  " + "   ".join(str(c + 1) for c in range(COLS)))
    lines.append(_TOP)

    for row in range(ROWS - 1, -1, -1):
        cells: list[str] = []
        for col in range(COLS):
            value = board[row][col]
            if (row, col) in highlight:
                cells.append(f" {_CYAN}{_BOLD}\u25cf{_RESET} ")   # ● cyan
            elif value == 1:
                cells.append(f" {_RED}\u25cf{_RESET} ")            # ● red
            elif value == 2:
                cells.append(f" {_YELLOW}\u25cf{_RESET} ")         # ● yellow
            else:
                cells.append("   ")
        lines.append("│" + "│".join(cells) + "│")
        if row > 0:
            lines.append(_SEP)

    lines.append(_BOT)
    return "\n".join(lines)


class TerminalUI:
    """Interactive terminal game loop."""

    def __init__(self, player1, player2) -> None:
        self.players = {1: player1, 2: player2}
        self._board_lines = 0  # lines occupied by the last board render

    def _draw(self, board, highlight=None, *, erase_above: int = 0) -> None:
        """Print the board, erasing the previous render plus `erase_above` extra lines."""
        total = self._board_lines + erase_above
        if total > 0:
            sys.stdout.write(f"\033[{total}F\033[J")
            sys.stdout.flush()
        rendered = render_board(board, highlight)
        print(rendered)
        self._board_lines = rendered.count("\n") + 1

    def run(self) -> None:
        game = ConnectFour()
        extra_erase = 0  # prompt lines to erase on next redraw

        try:
            while True:
                if not game.is_over:
                    self._draw(game.board, erase_above=extra_erase)
                    extra_erase = 0

                    player = self.players[game.current_player]
                    is_human = isinstance(player, HumanPlayer)
                    try:
                        col = player.get_move(game)
                    except UndoRequested:
                        _undo(game, count=2)
                        extra_erase = 1
                        continue
                    except QuitRequested:
                        print()
                        return

                    result = game.play(col)
                    extra_erase = 1 if is_human else 0

                    match result:
                        case MoveResult.Win(player=p, cells=cells):
                            self._draw(game.board, highlight=set(cells), erase_above=extra_erase)
                            extra_erase = 0
                            print(f"{self.players[p].name} wins!")
                            self._board_lines += 1
                        case MoveResult.Draw():
                            self._draw(game.board, erase_above=extra_erase)
                            extra_erase = 0
                            print("Draw!")
                            self._board_lines += 1
                    continue

                # Game over — offer undo or quit.
                raw = input("'u' to undo, 'q' to quit: ").strip().lower()
                if raw in ("u", "undo"):
                    extra_erase = 1
                    _undo(game, count=2)
                else:
                    return

        except (KeyboardInterrupt, EOFError):
            print()


def _undo(game: ConnectFour, count: int) -> None:
    undone = 0
    for _ in range(count):
        if not game.moves:
            break
        game.undo()
        undone += 1
    if undone == 0:
        print("Nothing to undo.")
