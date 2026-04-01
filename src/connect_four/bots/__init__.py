"""Bot implementations for Connect Four."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class Bot(Protocol):
    """Protocol that all bots must satisfy."""

    def next_move(self, moves: Sequence[int]) -> int: ...


from connect_four.bots.random import RandomBot
from connect_four.bots.first_available import FirstAvailableBot
from connect_four.bots.perfect import PerfectBot

__all__ = ["Bot", "RandomBot", "FirstAvailableBot", "PerfectBot"]
