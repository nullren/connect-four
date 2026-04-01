"""Tests for player abstractions."""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from connect_four.engine import ConnectFour
from connect_four.players import BotPlayer


class _GoodBot:
    """A bot that always returns column 3."""

    def next_move(self, moves: Sequence[int]) -> int:
        return 3


class _BadBot:
    """A bot that returns an invalid column."""

    def next_move(self, moves: Sequence[int]) -> int:
        return 99


class TestBotPlayer:
    def test_wraps_bot_and_returns_move(self) -> None:
        game = ConnectFour()
        player = BotPlayer(_GoodBot())
        col = player.get_move(game)
        assert col == 3

    def test_raises_value_error_on_invalid_column(self) -> None:
        game = ConnectFour()
        player = BotPlayer(_BadBot())
        with pytest.raises(ValueError, match="99"):
            player.get_move(game)

    def test_raises_runtime_error_when_game_is_over(self) -> None:
        game = ConnectFour()
        # Create a quick win for player 1:
        # P1 plays col 0, P2 plays col 1, P1 plays col 0, P2 plays col 1, ...
        for _ in range(3):
            game.play(0)  # P1
            game.play(1)  # P2
        game.play(0)  # P1 wins with 4 in col 0

        assert game.is_over

        player = BotPlayer(_GoodBot())
        with pytest.raises(RuntimeError, match=r"(?i)over"):
            player.get_move(game)

    def test_name_defaults_to_bot_class_name(self) -> None:
        player = BotPlayer(_GoodBot())
        assert player.name == "_GoodBot"

    def test_name_can_be_overridden(self) -> None:
        player = BotPlayer(_GoodBot(), name="MyBot")
        assert player.name == "MyBot"
