"""Tests for bot implementations."""

from __future__ import annotations

import sys

import pytest

from connect_four.bots.first_available import FirstAvailableBot
from connect_four.bots.perfect import PerfectBot
from connect_four.bots.random import RandomBot


class TestFirstAvailableBot:
    def test_returns_column_0_on_empty_board(self) -> None:
        bot = FirstAvailableBot()
        assert bot.next_move(()) == 0

    def test_skips_full_columns(self) -> None:
        bot = FirstAvailableBot()
        # Fill column 0: alternating players drop into col 0 six times
        # P1 drops col 0, P2 drops col 0, P1 drops col 0, ...
        moves = [0, 0, 0, 0, 0, 0]
        assert bot.next_move(moves) == 1


class TestRandomBot:
    def test_returns_valid_column(self) -> None:
        from connect_four.engine import COLS

        bot = RandomBot()
        for _ in range(50):
            col = bot.next_move(())
            assert 0 <= col < COLS

    def test_returns_valid_column_with_moves(self) -> None:
        from connect_four.engine import COLS

        bot = RandomBot()
        moves = [0, 0, 0, 0, 0, 0]  # col 0 full
        for _ in range(50):
            col = bot.next_move(moves)
            assert 1 <= col < COLS


class TestPerfectBot:
    def test_raises_when_rust_extension_missing(self, monkeypatch) -> None:
        """PerfectBot should raise RuntimeError if connect_four_rs is not importable."""
        # Ensure the module is not importable
        monkeypatch.setitem(sys.modules, "connect_four_rs", None)

        bot = PerfectBot(difficulty=3)
        with pytest.raises(RuntimeError, match="connect_four_rs"):
            bot.next_move(())

    def test_difficulty_from_string(self) -> None:
        bot = PerfectBot(difficulty="easy")
        assert bot._difficulty == 0

    def test_invalid_difficulty_string(self) -> None:
        with pytest.raises(ValueError):
            PerfectBot(difficulty="super")

    def test_invalid_difficulty_int(self) -> None:
        with pytest.raises(ValueError):
            PerfectBot(difficulty=5)
