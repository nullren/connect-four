"""Interactive terminal UI for Connect Four."""

from __future__ import annotations

from connect_four.engine import ConnectFour, MoveResult, ROWS, COLS

_RESET = "\033[0m"
_BOLD = "\033[1m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_DIM = "\033[2m"


def render_board(
    board: list[list[int]],
    highlight: set[tuple[int, int]] | None = None,
) -> str:
    """Render a Connect Four board as an ANSI-colored string.

    Row 0 (bottom of the board) is displayed at the bottom of output.
    """
    if highlight is None:
        highlight = set()

    lines: list[str] = []
    # Render from top row (ROWS-1) down to bottom row (0)
    for row in range(ROWS - 1, -1, -1):
        cells: list[str] = []
        for col in range(COLS):
            value = board[row][col]
            if (row, col) in highlight:
                cells.append(f"{_CYAN}{_BOLD}\u25cf{_RESET}")
            elif value == 1:
                cells.append(f"{_RED}\u25cf{_RESET}")
            elif value == 2:
                cells.append(f"{_YELLOW}\u25cf{_RESET}")
            else:
                cells.append(f"{_DIM}.{_RESET}")
        lines.append(" ".join(cells))

    # Column numbers 1-7
    lines.append(" ".join(str(c + 1) for c in range(COLS)))
    return "\n".join(lines)


class TerminalUI:
    """Interactive terminal game loop."""

    def __init__(self, player1, player2) -> None:
        self.players = {1: player1, 2: player2}

    def run(self) -> None:
        game = ConnectFour()
        while not game.is_over:
            print(render_board(game.board))
            player = self.players[game.current_player]
            col = player.get_move(game)
            result = game.play(col)
            match result:
                case MoveResult.Win(player=p, cells=cells):
                    print(render_board(game.board, highlight=set(cells)))
                    winner_name = self.players[p].name
                    print(f"{winner_name} wins!")
                case MoveResult.Draw():
                    print(render_board(game.board))
                    print("Draw!")
