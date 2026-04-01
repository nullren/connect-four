"""Monte Carlo Tree Search bot."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence

from connect_four.bots import register
from connect_four.engine import ConnectFour


class _MCTSNode:
    __slots__ = ("children", "moves", "parent", "visits", "wins")

    def __init__(self, moves: tuple[int, ...], parent: _MCTSNode | None) -> None:
        self.moves = moves
        self.parent = parent
        self.children: dict[int, _MCTSNode] = {}
        self.wins: float = 0.0
        self.visits: int = 0

    def unexplored_moves(self, valid: list[int]) -> list[int]:
        return [col for col in valid if col not in self.children]

    def ucb1(self, c: float = math.sqrt(2)) -> float:
        if self.visits == 0:
            return float("inf")
        if self.parent is None or self.parent.visits == 0:
            return float("inf")
        return self.wins / self.visits + c * math.sqrt(math.log(self.parent.visits) / self.visits)


class MCTSBot:
    """Monte Carlo Tree Search. Configurable simulation count (default 300)."""

    def __init__(self, simulations: int = 300) -> None:
        self._simulations = simulations

    @property
    def name(self) -> str:
        return "mcts"

    @property
    def description(self) -> str:
        return f"Monte Carlo Tree Search ({self._simulations} simulations per move)."

    def next_move(self, moves: Sequence[int]) -> int:
        root = _MCTSNode(tuple(moves), parent=None)

        for _ in range(self._simulations):
            node = self._select(root)
            node = self._expand(node)
            result = self._rollout(node.moves)
            self._backpropagate(node, result)

        # Pick the column with the most visits (robust child selection).
        return max(root.children, key=lambda c: root.children[c].visits)

    def _select(self, node: _MCTSNode) -> _MCTSNode:
        game = ConnectFour.from_moves(node.moves)
        while not game.is_over:
            unexplored = node.unexplored_moves(game.valid_moves)
            if unexplored:
                return node
            best_col = max(node.children, key=lambda c: node.children[c].ucb1())
            node = node.children[best_col]
            game.play(best_col)
        return node

    def _expand(self, node: _MCTSNode) -> _MCTSNode:
        game = ConnectFour.from_moves(node.moves)
        if game.is_over:
            return node
        unexplored = node.unexplored_moves(game.valid_moves)
        col = random.choice(unexplored)
        child = _MCTSNode((*node.moves, col), parent=node)
        node.children[col] = child
        return child

    def _rollout(self, moves: tuple[int, ...]) -> float | None:
        """Random playout from *moves* to terminal state.

        Returns 1.0 if Player ONE wins, -1.0 if Player TWO wins, None for draw.
        """
        game = ConnectFour.from_moves(moves)
        while not game.is_over:
            col = random.choice(game.valid_moves)
            game.play(col)

        if game.winner is None:
            return None
        return 1.0 if game.winner == 1 else -1.0

    def _backpropagate(self, node: _MCTSNode | None, result: float | None) -> None:
        """Walk up to root incrementing visits and crediting wins.

        A node's "mover" is the player who made the last move to *arrive* at
        that node, i.e. player ONE if len(moves) is odd.
        """
        while node is not None:
            node.visits += 1
            if result is not None:
                mover_is_one = len(node.moves) % 2 == 1
                if (mover_is_one and result > 0) or (not mover_is_one and result < 0):
                    node.wins += 1.0
            node = node.parent


register(MCTSBot())
