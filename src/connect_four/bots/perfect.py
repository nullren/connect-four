"""A bot backed by the Rust perfect-play engine."""

from __future__ import annotations

from collections.abc import Sequence

DIFFICULTIES: dict[str, int] = {
    "easy": 0,
    "medium": 1,
    "hard": 2,
    "impossible": 3,
}


class PerfectBot:
    """Uses the Rust connect_four_rs extension for perfect play."""

    def __init__(self, difficulty: int | str = 3) -> None:
        if isinstance(difficulty, str):
            key = difficulty.lower()
            if key not in DIFFICULTIES:
                raise ValueError(
                    f"Unknown difficulty {difficulty!r}. "
                    f"Choose from: {', '.join(DIFFICULTIES)}"
                )
            self._difficulty = DIFFICULTIES[key]
        else:
            if not (0 <= difficulty <= 3):
                raise ValueError(f"Difficulty must be 0-3, got {difficulty}")
            self._difficulty = int(difficulty)

    def next_move(self, moves: Sequence[int]) -> int:
        try:
            import connect_four_rs  # lazy import
        except ImportError as exc:
            raise RuntimeError(
                "The Rust extension 'connect_four_rs' is not installed. "
                "Run 'uv run maturin develop' to compile it."
            ) from exc

        result = connect_four_rs.best_move(list(moves), self._difficulty)
        if result is None:
            raise RuntimeError(
                "connect_four_rs.best_move returned None — "
                "the game may already be over."
            )
        return result
