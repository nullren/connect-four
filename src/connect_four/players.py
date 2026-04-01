"""Player abstractions for Connect Four."""

from __future__ import annotations

from connect_four.engine import ConnectFour


class BotPlayer:
    """Wraps a bot object and validates its moves."""

    def __init__(self, bot: object, name: str | None = None) -> None:
        self.bot = bot
        self.name: str = name if name is not None else type(bot).__name__

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
        # Display 1-based columns to the user
        display_cols = [c + 1 for c in valid]

        while True:
            try:
                raw = input(
                    f"{self.name}, choose a column {display_cols}: "
                )
                col_1based = int(raw)
                col = col_1based - 1
                if col in valid:
                    return col
                print(f"Column {col_1based} is not available. Try again.")
            except ValueError:
                print("Please enter a number.")
            except EOFError:
                print()
                raise
