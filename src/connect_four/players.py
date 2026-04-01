"""Player abstractions for Connect Four."""

from __future__ import annotations

from connect_four.engine import ConnectFour


class UndoRequested(Exception):
    """Raised by HumanPlayer when the user requests an undo."""


class QuitRequested(Exception):
    """Raised by HumanPlayer when the user requests to quit."""


class BotPlayer:
    """Wraps a bot object and validates its moves."""

    def __init__(self, bot: object, name: str | None = None) -> None:
        self.bot = bot
        self.name: str = name if name is not None else getattr(bot, "name", type(bot).__name__)

    def get_move(self, game: ConnectFour) -> int:
        if game.is_over:
            raise RuntimeError("Cannot get move: the game is already over.")

        col = self.bot.next_move(game.moves)  # type: ignore[union-attr]

        if col not in game.valid_moves:
            raise ValueError(
                f"Bot {self.name!r} returned invalid column {col}. "
                f"Valid columns: {game.valid_moves}"
            )
        return col


class HumanPlayer:
    """Prompts a human for input via the terminal."""

    def __init__(self, name: str = "Human") -> None:
        self.name = name

    def get_move(self, game: ConnectFour) -> int:
        valid = game.valid_moves
        display_cols = [c + 1 for c in valid]
        can_undo = len(game.moves) > 0

        hints = ["'q' to quit"]
        if can_undo:
            hints.insert(0, "'u' to undo")
        prompt = f"{self.name}, column {display_cols} ({', '.join(hints)}): "

        while True:
            try:
                raw = input(prompt).strip().lower()
                if raw in ("q", "quit"):
                    raise QuitRequested
                if raw in ("u", "undo"):
                    if can_undo:
                        raise UndoRequested
                    print("Nothing to undo.")
                    continue
                col = int(raw) - 1
                if col in valid:
                    return col
                print(f"Column {int(raw)} is not available. Try again.")
            except ValueError:
                print("Please enter a number.")
            except EOFError:
                print()
                raise QuitRequested from None
