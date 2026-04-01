"""CLI entry point for Connect Four."""

from __future__ import annotations

import argparse

from connect_four.bots import get_registry
from connect_four.bots.perfect import PerfectBot
from connect_four.players import BotPlayer, HumanPlayer

DIFFICULTIES = ["easy", "medium", "hard", "impossible"]

# Bot types and player types are derived from the registry at startup,
# so new bots added to bots/ appear automatically.
_BOT_REGISTRY = get_registry()
BOT_TYPES = list(_BOT_REGISTRY.keys())
PLAYER_TYPES = ["human", *BOT_TYPES]


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
    raise argparse.ArgumentTypeError(f"difficulty must be 0-3 or one of: {', '.join(DIFFICULTIES)}")


def _make_bot_player(kind: str, difficulty: int | str, suffix: str = "") -> BotPlayer:
    """Instantiate a bot by registry name. PerfectBot gets the difficulty param."""
    name = kind + suffix
    if kind == "perfect":
        return BotPlayer(PerfectBot(difficulty=difficulty), name=name)
    bot = _BOT_REGISTRY[kind]
    return BotPlayer(bot, name=name)


def _make_player(kind: str, difficulty: int | str) -> HumanPlayer | BotPlayer:
    if kind == "human":
        return HumanPlayer(name="Human")
    return _make_bot_player(kind, difficulty)


def _bot_pair(p1_type: str, p2_type: str, difficulty: int | str) -> tuple[BotPlayer, BotPlayer]:
    """Create two bot players, disambiguating names when they're the same type."""
    if p1_type == p2_type:
        return (
            _make_bot_player(p1_type, difficulty, suffix=" (1)"),
            _make_bot_player(p2_type, difficulty, suffix=" (2)"),
        )
    return _make_bot_player(p1_type, difficulty), _make_bot_player(p2_type, difficulty)


def _bots_epilog() -> str:
    lines = ["available bots:"]
    for name, bot in _BOT_REGISTRY.items():
        lines.append(f"  {name:<16} {bot.description}")
    lines += ["", "difficulty:  easy, medium, hard, impossible  (or 0-3)"]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="connect-four",
        description="Connect Four — play interactively or benchmark bots",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_bots_epilog(),
    )
    subparsers = parser.add_subparsers(dest="command")

    # play subcommand
    play_parser = subparsers.add_parser("play", help="Play an interactive game")
    play_parser.add_argument(
        "--p1",
        default="human",
        choices=PLAYER_TYPES,
        metavar="TYPE",
        help="player 1 type (default: human)",
    )
    play_parser.add_argument(
        "--p2",
        default="human",
        choices=PLAYER_TYPES,
        metavar="TYPE",
        help="player 2 type (default: human)",
    )
    play_parser.add_argument(
        "--difficulty",
        default="impossible",
        type=_parse_difficulty,
        metavar="LEVEL",
        help="bot difficulty: easy/medium/hard/impossible or 0-3 (default: impossible)",
    )

    # benchmark subcommand
    bench_parser = subparsers.add_parser("benchmark", help="Run bot-vs-bot benchmark")
    bench_parser.add_argument(
        "--p1",
        default="perfect",
        choices=BOT_TYPES,
        metavar="TYPE",
        help="bot 1 type (default: perfect)",
    )
    bench_parser.add_argument(
        "--p2",
        default="random",
        choices=BOT_TYPES,
        metavar="TYPE",
        help="bot 2 type (default: random)",
    )
    bench_parser.add_argument(
        "--games", type=int, default=100, metavar="N", help="number of games to play (default: 100)"
    )
    bench_parser.add_argument(
        "--difficulty",
        default="impossible",
        type=_parse_difficulty,
        metavar="LEVEL",
        help="bot difficulty: easy/medium/hard/impossible or 0-3 (default: impossible)",
    )
    bench_parser.add_argument("--verbose", action="store_true", help="print result of each game")

    args = parser.parse_args()

    if args.command is None or args.command == "play":
        p1_type = getattr(args, "p1", "human")
        p2_type = getattr(args, "p2", "human")
        difficulty = getattr(args, "difficulty", "impossible")

        player1 = _make_player(p1_type, difficulty)
        player2 = _make_player(p2_type, difficulty)

        # Disambiguate if two bots have the same name
        if player1.name == player2.name:
            player1.name = player1.name + " (1)"
            player2.name = player2.name + " (2)"

        from connect_four.ui.terminal import TerminalUI

        TerminalUI(player1, player2).run()

    elif args.command == "benchmark":
        bot1, bot2 = _bot_pair(args.p1, args.p2, args.difficulty)

        from connect_four.ui.benchmark import BenchmarkUI

        BenchmarkUI(bot1, bot2).run(n_games=args.games, verbose=args.verbose)


if __name__ == "__main__":
    main()
