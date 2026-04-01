"""CLI entry point for Connect Four."""

from __future__ import annotations

import argparse
import sys

from connect_four.players import HumanPlayer, BotPlayer
from connect_four.bots import RandomBot, FirstAvailableBot, PerfectBot

PLAYER_TYPES = ["human", "perfect", "random", "first"]
BOT_TYPES = ["perfect", "random", "first"]
DIFFICULTIES = ["easy", "medium", "hard", "impossible"]

BOT_NAMES = {
    "perfect": "Perfect",
    "random": "Random",
    "first": "First",
}


def _parse_difficulty(value: str) -> int | str:
    """Accept difficulty as 0-3 or easy/medium/hard/impossible."""
    if value in DIFFICULTIES:
        return value
    try:
        n = int(value)
        if 0 <= n <= 3:
            return n
    except ValueError:
        pass
    raise argparse.ArgumentTypeError(
        f"difficulty must be 0-3 or one of: {', '.join(DIFFICULTIES)}"
    )


def _make_bot_player(kind: str, name: str, difficulty: int | str) -> BotPlayer:
    match kind:
        case "perfect":
            return BotPlayer(PerfectBot(difficulty=difficulty), name=name)
        case "random":
            return BotPlayer(RandomBot(), name=name)
        case "first":
            return BotPlayer(FirstAvailableBot(), name=name)


def _make_player(kind: str, name: str, difficulty: int | str) -> HumanPlayer | BotPlayer:
    if kind == "human":
        return HumanPlayer(name=name)
    return _make_bot_player(kind, name, difficulty)


def _bot_names(p1_type: str, p2_type: str) -> tuple[str, str]:
    """Return names for two bots, disambiguating if they're the same type."""
    n1 = BOT_NAMES[p1_type]
    n2 = BOT_NAMES[p2_type]
    if n1 == n2:
        return f"{n1} (1)", f"{n2} (2)"
    return n1, n2


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="connect-four",
        description="Connect Four — play interactively or benchmark bots",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "player types:  human, perfect, random, first\n"
            "difficulty:    easy, medium, hard, impossible  (or 0-3)\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    # play subcommand
    play_parser = subparsers.add_parser("play", help="Play an interactive game")
    play_parser.add_argument("--p1", default="human", choices=PLAYER_TYPES, metavar="TYPE",
                             help="player 1 type (default: human)")
    play_parser.add_argument("--p2", default="human", choices=PLAYER_TYPES, metavar="TYPE",
                             help="player 2 type (default: human)")
    play_parser.add_argument("--difficulty", default="impossible", type=_parse_difficulty, metavar="LEVEL",
                             help="bot difficulty: easy/medium/hard/impossible or 0-3 (default: impossible)")

    # benchmark subcommand
    bench_parser = subparsers.add_parser("benchmark", help="Run bot-vs-bot benchmark")
    bench_parser.add_argument("--p1", default="perfect", choices=BOT_TYPES, metavar="TYPE",
                              help="bot 1 type (default: perfect)")
    bench_parser.add_argument("--p2", default="random", choices=BOT_TYPES, metavar="TYPE",
                              help="bot 2 type (default: random)")
    bench_parser.add_argument("--games", type=int, default=100, metavar="N",
                              help="number of games to play (default: 100)")
    bench_parser.add_argument("--difficulty", default="impossible", type=_parse_difficulty, metavar="LEVEL",
                              help="bot difficulty: easy/medium/hard/impossible or 0-3 (default: impossible)")
    bench_parser.add_argument("--verbose", action="store_true",
                              help="print result of each game")

    args = parser.parse_args()

    if args.command is None or args.command == "play":
        p1_type = getattr(args, "p1", "human")
        p2_type = getattr(args, "p2", "human")
        difficulty = getattr(args, "difficulty", "impossible")

        # Human players get "Player 1" / "Player 2"; bots get their strategy name
        p1_name = "Player 1" if p1_type == "human" else BOT_NAMES[p1_type]
        p2_name = "Player 2" if p2_type == "human" else BOT_NAMES[p2_type]
        if p1_name == p2_name:
            p1_name, p2_name = f"{p1_name} (1)", f"{p2_name} (2)"

        player1 = _make_player(p1_type, p1_name, difficulty)
        player2 = _make_player(p2_type, p2_name, difficulty)

        from connect_four.ui.terminal import TerminalUI
        TerminalUI(player1, player2).run()

    elif args.command == "benchmark":
        name1, name2 = _bot_names(args.p1, args.p2)
        bot1 = _make_bot_player(args.p1, name1, args.difficulty)
        bot2 = _make_bot_player(args.p2, name2, args.difficulty)

        from connect_four.ui.benchmark import BenchmarkUI
        BenchmarkUI(bot1, bot2).run(n_games=args.games, verbose=args.verbose)


if __name__ == "__main__":
    main()
