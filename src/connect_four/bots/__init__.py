"""Bot protocol, registry, and auto-discovery."""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class Bot(Protocol):
    """Protocol that all bots must satisfy."""

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    def next_move(self, moves: Sequence[int]) -> int: ...


_registry: dict[str, Bot] = {}


def register(bot: Bot) -> Bot:
    """Register a bot instance by its name. Called by each bot module."""
    _registry[bot.name] = bot
    return bot


def get_registry() -> dict[str, Bot]:
    """Return a copy of the bot registry."""
    return dict(_registry)


def get_bot(name: str) -> Bot:
    """Look up a registered bot by name. Raises KeyError if not found."""
    return _registry[name]


# Auto-discover and import all bot modules in this package.
# Any .py file dropped into bots/ will be picked up automatically —
# no changes to this file required.
for _mod in pkgutil.iter_modules(__path__):
    importlib.import_module(f"connect_four.bots.{_mod.name}")
