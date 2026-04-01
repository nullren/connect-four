"""Bot-vs-bot benchmark UI for Connect Four."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from connect_four.engine import ConnectFour


@dataclass
class BenchmarkResult:
    """Stores results of a bot-vs-bot benchmark run."""

    bot1_name: str
    bot2_name: str
    n_games: int
    bot1_wins: int = 0
    bot2_wins: int = 0
    draws: int = 0
    bot1_wins_as_p1: int = 0
    bot1_wins_as_p2: int = 0
    bot2_wins_as_p1: int = 0
    bot2_wins_as_p2: int = 0
    draws_bot1_first: int = 0
    draws_bot2_first: int = 0
    bot1_think_time: float = 0.0
    bot2_think_time: float = 0.0
    bot1_moves: int = 0
    bot2_moves: int = 0

    def print_summary(self) -> None:
        """Print a formatted summary of the benchmark results."""
        def pct(n: int) -> str:
            return f"{n / self.n_games * 100:.1f}%" if self.n_games else "0.0%"

        def avg_ms(total_s: float, moves: int) -> str:
            if moves == 0:
                return "n/a"
            return f"{total_s / moves * 1000:.1f}ms"

        half = self.n_games // 2 or 1

        print(f"\n{'=' * 50}")
        print(f"Benchmark: {self.bot1_name} vs {self.bot2_name}")
        print(f"Games played: {self.n_games}")
        print(f"{'=' * 50}")

        print(f"\nOverall:")
        print(f"  {self.bot1_name} wins: {self.bot1_wins} ({pct(self.bot1_wins)})")
        print(f"  {self.bot2_name} wins: {self.bot2_wins} ({pct(self.bot2_wins)})")
        print(f"  Draws:           {self.draws} ({pct(self.draws)})")

        print(f"\nWhen {self.bot1_name} goes first ({half} games):")
        print(f"  {self.bot1_name} wins: {self.bot1_wins_as_p1}")
        print(f"  {self.bot2_name} wins: {self.bot2_wins_as_p2}")
        print(f"  Draws:           {self.draws_bot1_first}")

        print(f"\nWhen {self.bot2_name} goes first ({half} games):")
        print(f"  {self.bot2_name} wins: {self.bot2_wins_as_p1}")
        print(f"  {self.bot1_name} wins: {self.bot1_wins_as_p2}")
        print(f"  Draws:           {self.draws_bot2_first}")

        print(f"\nThink time:")
        print(f"  {self.bot1_name}: {self.bot1_think_time:.3f}s total, "
              f"{avg_ms(self.bot1_think_time, self.bot1_moves)} avg/move "
              f"({self.bot1_moves} moves)")
        print(f"  {self.bot2_name}: {self.bot2_think_time:.3f}s total, "
              f"{avg_ms(self.bot2_think_time, self.bot2_moves)} avg/move "
              f"({self.bot2_moves} moves)")
        print()


class BenchmarkUI:
    """Run bot-vs-bot games and collect statistics."""

    def __init__(self, bot1, bot2) -> None:
        self.bot1 = bot1
        self.bot2 = bot2

    def run(self, n_games: int = 100, verbose: bool = False) -> BenchmarkResult:
        result = BenchmarkResult(
            bot1_name=self.bot1.name,
            bot2_name=self.bot2.name,
            n_games=n_games,
        )

        for game_index in range(n_games):
            # Alternate starting player: even index -> bot1 is player 1
            if game_index % 2 == 0:
                players = {1: self.bot1, 2: self.bot2}
                bot1_is_player = 1
            else:
                players = {1: self.bot2, 2: self.bot1}
                bot1_is_player = 2

            game = ConnectFour()
            while not game.is_over:
                player = players[game.current_player]
                is_bot1 = player is self.bot1

                t0 = time.perf_counter()
                col = player.get_move(game)
                elapsed = time.perf_counter() - t0

                if is_bot1:
                    result.bot1_think_time += elapsed
                    result.bot1_moves += 1
                else:
                    result.bot2_think_time += elapsed
                    result.bot2_moves += 1

                game.play(col)

            winner = game.winner
            if winner is None:
                result.draws += 1
                if bot1_is_player == 1:
                    result.draws_bot1_first += 1
                else:
                    result.draws_bot2_first += 1
            elif winner == bot1_is_player:
                result.bot1_wins += 1
                if bot1_is_player == 1:
                    result.bot1_wins_as_p1 += 1
                else:
                    result.bot1_wins_as_p2 += 1
            else:
                result.bot2_wins += 1
                if bot1_is_player == 1:
                    result.bot2_wins_as_p2 += 1
                else:
                    result.bot2_wins_as_p1 += 1

            if verbose:
                winner_name = (
                    "Draw"
                    if winner is None
                    else (result.bot1_name if winner == bot1_is_player else result.bot2_name)
                )
                starter = result.bot1_name if bot1_is_player == 1 else result.bot2_name
                print(f"Game {game_index + 1}/{n_games}: {winner_name} (first: {starter})")

        result.print_summary()
        return result
