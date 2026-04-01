# Connect Four

A Connect Four game in Python with a Rust-powered perfect-play bot.

```
  1   2   3   4   5   6   7
┌───┬───┬───┬───┬───┬───┬───┐
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │   │ ● │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │ ● │ ● │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │ ● │ ● │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│ ● │   │ ● │ ● │ ● │   │   │
└───┴───┴───┴───┴───┴───┴───┘
```

## Dependencies

| Tool | Purpose |
|------|---------|
| [Python 3.13+](https://python.org) | Runtime |
| [Rust](https://rustup.rs) | Compiling the perfect-play bot |
| [uv](https://docs.astral.sh/uv/) | Python package manager |
| [maturin](https://maturin.rs) | Build backend for Rust extensions |

Or skip all of the above and use Docker.

## Getting started

```sh
# Install Python deps and compile the Rust extension
uv sync
uv run maturin develop --release

# Play against the perfect bot
uv run connect-four play --p2 perfect

# Human vs human
uv run connect-four play

# Bot vs bot
uv run connect-four play --p1 minimax --p2 mcts
```

## Bots

| Name | Description |
|------|-------------|
| `perfect` | Rust-backed solver using `connect-four-ai`. Supports difficulty levels. |
| `minimax` | Alpha-beta pruning, depth 6, with center-first move ordering and transposition cache. |
| `mcts` | Monte Carlo Tree Search, 300 simulations per move, UCB1 selection. |
| `random` | Picks a random valid column. |
| `first` | Always picks the leftmost valid column. |

## CLI reference

### `play`

```sh
uv run connect-four play [--p1 TYPE] [--p2 TYPE] [--difficulty LEVEL]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--p1` | `human` | Player 1 type (`human`, `perfect`, `minimax`, `mcts`, `random`, `first`) |
| `--p2` | `human` | Player 2 type |
| `--difficulty` | `impossible` | Bot difficulty: `easy`, `medium`, `hard`, `impossible` or `0`–`3` |

During play, at your turn:
- Enter a column number (`1`–`7`) to place a piece
- `u` — undo the last 2 moves (your move + the opponent's response)
- `q` / Ctrl-C / Ctrl-D — quit
- After the game ends, `u` to undo or Enter/`q` to quit

Think time per player is shown at the end of each game.

### `benchmark`

```sh
uv run connect-four benchmark [--p1 TYPE] [--p2 TYPE] [--games N] [--difficulty LEVEL] [--verbose]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--p1` | `perfect` | Bot 1 type |
| `--p2` | `random` | Bot 2 type |
| `--games` | `100` | Number of games to play |
| `--difficulty` | `impossible` | Difficulty for the `perfect` bot |
| `--verbose` | off | Print the result of each game |

Example:

```sh
uv run connect-four benchmark --p1 minimax --p2 mcts --games 50 --verbose
```

## Running tests

```sh
uv run pytest
uv run pytest --cov=connect_four    # with coverage
```

## Docker

Build and run without installing any local dependencies:

```sh
docker build -t connect-four .

# Interactive game (human vs perfect bot)
docker run -it connect-four play --p2 perfect

# Benchmark
docker run connect-four benchmark --p1 minimax --p2 random --games 20
```

## Adding a new bot

1. Create `src/connect_four/bots/my_bot.py`
2. Implement the `Bot` protocol (`name`, `description`, `next_move`)
3. Call `register(MyBot())` at module level

That's it — the bot appears automatically in the CLI and benchmark.

```python
from connect_four.bots import register
from connect_four.engine import ConnectFour
from collections.abc import Sequence

class MyBot:
    @property
    def name(self) -> str:
        return "mybot"

    @property
    def description(self) -> str:
        return "Does something clever."

    def next_move(self, moves: Sequence[int]) -> int:
        game = ConnectFour.from_moves(moves)
        return game.valid_moves[0]

register(MyBot())
```

## License

MIT
