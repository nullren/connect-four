# Connect Four — Implementation Plan

## Overview

A Connect Four game in Python with a Rust-powered perfect-play bot. The core
game engine is a `ConnectFour` class that encapsulates all game state as an
internal move history (`list[int]` of columns). All board state is derived on
demand. Two UI modes share the same engine: an interactive terminal UI and a
headless benchmark UI for bot-vs-bot statistics.

## Architecture

```
                   ┌──────────────┐
                   │  __main__.py │   CLI entry point (argparse)
                   └──────┬───────┘
                          │
              ┌───────────┼───────────┐
              │                       │
     ┌────────▼────────┐    ┌────────▼────────┐
     │  terminal.py    │    │  benchmark.py   │   UI layer
     └────────┬────────┘    └────────┬────────┘
              │                       │
              └───────────┬───────────┘
                          │
              ┌───────────▼───────────┐
              │     players.py        │   HumanPlayer / BotPlayer
              └───────────┬───────────┘
                          │
              ┌───────────▼───────────┐
              │      bots/            │   RandomBot / FirstAvailableBot / PerfectBot
              └───────────┬───────────┘
                          │
          ┌───────────────┼───────────────┐
          │                               │
 ┌────────▼────────┐           ┌──────────▼──────────┐
 │   engine.py     │           │  connect_four_rs    │
 │  (pure Python)  │           │  (Rust via PyO3)    │
 └─────────────────┘           └─────────────────────┘
```

## Project Structure

```
connect-four/
├── pyproject.toml               # uv + maturin build config
├── Cargo.toml                   # workspace root
├── .python-version              # 3.13
├── .gitignore
├── PLAN.md
├── src/
│   ├── connect_four/            # Python package
│   │   ├── __init__.py
│   │   ├── __main__.py          # CLI: play / benchmark subcommands
│   │   ├── engine.py            # Pure game logic (the heart)
│   │   ├── players.py           # HumanPlayer, BotPlayer
│   │   ├── bots/                # Bot implementations (one per file)
│   │   │   ├── __init__.py      # Bot protocol + re-exports all bots
│   │   │   ├── random.py        # RandomBot
│   │   │   ├── first_available.py  # FirstAvailableBot
│   │   │   └── perfect.py       # PerfectBot (Rust-backed)
│   │   └── ui/
│   │       ├── __init__.py
│   │       ├── terminal.py      # Interactive terminal game
│   │       └── benchmark.py     # Bot-vs-bot statistics
│   └── connect_four_rs/         # Rust crate (not a Python package)
│       ├── Cargo.toml
│       └── src/
│           └── lib.rs           # PyO3 bindings wrapping connect-four-ai
└── tests/
    ├── __init__.py
    ├── test_engine.py
    ├── test_bots.py
    └── test_players.py
```

## Key Design Decisions

### 1. ConnectFour class owns the move history

The game engine is a `ConnectFour` class. Internally it stores a `list[int]` of
0-based column indices (one per turn, alternating players). This list is the
only mutable state. All other information — board grid, winner, valid moves —
is derived on demand via properties/methods.

Callers never manage the move list directly. Instead:

```python
game = ConnectFour()
result = game.drop_token(3)   # MoveResult.Ongoing, .Win, .Draw, or .InvalidMove
result = game.drop_token(2)
game.undo()                   # pops last move
game.board                    # derived 6x7 grid
game.current_player           # 1 or 2
game.valid_moves              # list of playable columns
game.moves                    # read-only Sequence[int] view of history
```

This design keeps all mutation behind a clean API while still enabling undo,
replay, and passing the history to bots.

### 2. MoveResult as the return type of drop_token

`drop_token(col)` returns a `MoveResult` — a discriminated union:

```python
match game.drop_token(col):
    case MoveResult.Ongoing(player=next_player):
        ...
    case MoveResult.Win(player=winner, cells=[(r,c), ...]):
        ...
    case MoveResult.Draw():
        ...
    case MoveResult.InvalidMove(reason="..."):
        ...
```

No exceptions for invalid moves — the result type makes all outcomes explicit.

### 3. Engine is pure and dependency-free

`engine.py` imports nothing from the rest of the project. No Rust, no UI, no
player types. `ConnectFour` plus `MoveResult` plus the `build_board()` utility
function are the entire public API. This makes it trivially testable and the
single source of truth for game rules.

`build_board(moves)` is also exported as a standalone utility — bots or other
code that has a move list can derive a board without constructing a full
`ConnectFour` instance.

### 4. Rust extension is minimal

The `connect_four_rs` module exposes exactly two functions:

```python
def best_move(moves: list[int], difficulty: int) -> int | None: ...
def all_move_scores(moves: list[int]) -> list[int | None]: ...
```

No Python classes wrapping Rust types. The Rust layer converts our 0-based
`list[int]` into a `Position` via `play()` calls and delegates to `AIPlayer`.

### 5. Bot protocol + extensible bots/ package

```python
class Bot(Protocol):
    def next_move(self, moves: Sequence[int]) -> int: ...
```

Bots receive the move history as a read-only `Sequence[int]`. That's the
minimal, complete input — if a bot wants a board grid, it can call
`build_board()` itself. This keeps the interface lean and avoids the engine
deciding what derived views a bot needs.

`BotPlayer` wraps a `Bot` and validates its output against `valid_moves`.

Bots live in `bots/`, one strategy per file. The `Bot` protocol lives in
`bots/__init__.py` alongside re-exports of all concrete bots. Adding a new bot
means: create a new file in `bots/`, implement `next_move`, add a re-export in
`__init__.py`.

### 6. Players are duck-typed

Both `HumanPlayer` and `BotPlayer` expose
`get_move(game: ConnectFour) -> int`. No shared base class — the game loop
uses duck typing. Players receive the whole `ConnectFour` object so they can
access `game.moves`, `game.valid_moves`, `game.current_player`, etc.

### 7. Column indexing

Internal: **0-based** everywhere (engine, bots, Rust).
Terminal UI display: **1-based** (columns 1-7 shown to user, converted at the
boundary in `HumanPlayer` and `render_board`).

---

## Verified Rust Crate API

Crate: [`connect-four-ai`](https://crates.io/crates/connect-four-ai) v1.0.0

**Position** (0-based columns):
- `Position::new() -> Position`
- `Position::WIDTH: usize = 7`, `HEIGHT: usize = 6`
- `pos.play(&mut self, col: usize)` — 0-based
- `pos.is_playable(&self, col: usize) -> bool`
- `pos.is_won_position(&self) -> bool` — checks both players
- `pos.is_winning_move(&self, col: usize) -> bool`
- `pos.get_moves(&self) -> usize`

**AIPlayer**:
- `AIPlayer::new(difficulty: Difficulty) -> AIPlayer`
- `player.get_move(&mut self, &Position) -> Option<usize>` — 0-based column
- `player.get_all_move_scores(&mut self, &Position) -> [Option<i8>; 7]`

**Difficulty**: `Easy`, `Medium`, `Hard`, `Impossible`

---

## File Specifications

### `engine.py` — Pure Game Logic

**Constants:** `ROWS = 6`, `COLS = 7`, `WIN_LENGTH = 4`, `MAX_MOVES = 42`

**`MoveResult`** — discriminated union (dataclass variants):
- `MoveResult.Ongoing(player: int)` — game continues, `player` is next to move
- `MoveResult.Win(player: int, cells: list[tuple[int, int]])` — `player` won,
  `cells` is the four winning positions
- `MoveResult.Draw()` — board full, no winner
- `MoveResult.InvalidMove(reason: str)` — column out of range, full, or game
  already over

**`ConnectFour`** — the game engine:
- `ConnectFour()` — new game, empty board
- `game.drop_token(col: int) -> MoveResult` — play a move, returns result
- `game.undo() -> None` — pop last move (raises if no moves)
- `game.moves -> Sequence[int]` — read-only view of move history
- `game.board -> list[list[int]]` — derived 6x7 grid, board[row][col],
  row 0 = bottom, values 0/1/2
- `game.current_player -> int` — 1 or 2
- `game.valid_moves -> list[int]` — playable columns, `[]` if game over
- `game.is_over -> bool` — True if won or drawn
- `game.winner -> int | None` — 1, 2, or None

**Standalone utility:**
- `build_board(moves: Sequence[int]) -> list[list[int]]` — derive board from
  any move list. Public utility for bots and other code that has a move
  sequence without a full `ConnectFour` instance.

Win detection: scans horizontal, vertical, and both diagonals after each move.

### `players.py` — Player Abstractions

**`BotPlayer`**:
- `__init__(self, bot: Bot, name: str | None = None)`
- `get_move(self, game: ConnectFour) -> int` — calls `bot.next_move(game.moves)`,
  validates output against `game.valid_moves`

**`HumanPlayer`**:
- `__init__(self, name: str = "Human")`
- `get_move(self, game: ConnectFour) -> int` — prompts for 1-based column,
  loops until valid, returns 0-based

### `bots/` — Bot Implementations (one strategy per file)

**`bots/__init__.py`**: defines the `Bot` protocol and re-exports all concrete
bot classes for convenient imports:
```python
from connect_four.bots.random import RandomBot
from connect_four.bots.first_available import FirstAvailableBot
from connect_four.bots.perfect import PerfectBot
```

**`bots/random.py`** — `RandomBot`: picks uniformly at random from
`build_board`-derived valid moves (or uses `ConnectFour` static helpers).

**`bots/first_available.py`** — `FirstAvailableBot`: always picks leftmost
valid column. Deterministic, useful for tests.

**`bots/perfect.py`** — `PerfectBot`:
- `__init__(self, difficulty: int | str = 3)` — 0=Easy..3=Impossible, or
  string name
- Lazily imports `connect_four_rs` inside `next_move()` so the package is
  importable even without the compiled extension.
- Passes `list(moves)` straight to `connect_four_rs.best_move()`.

To add a new bot: create `bots/my_strategy.py`, implement `next_move(self,
moves: Sequence[int]) -> int`, add a re-export in `bots/__init__.py`.

### `connect_four_rs` (Rust)

**`best_move(moves: Vec<i64>, difficulty: u8) -> Option<usize>`**:
1. Build `Position` from moves via `Position::new()` + `play()` loop
2. Validate each move (range, playable, not already won)
3. Create `AIPlayer::new(difficulty)` and call `get_move(&pos)`

**`all_move_scores(moves: Vec<i64>) -> Vec<Option<i8>>`**:
Same position building, then `get_all_move_scores(&pos)`.

### `ui/terminal.py` — Interactive Terminal

**`render_board(board, highlight=None) -> str`**: ANSI-colored board, row 0 at
bottom, 1-based column numbers. Red for P1, yellow for P2, cyan for winning
cells.

**`TerminalUI`**:
- `__init__(self, player1, player2)` — any mix of HumanPlayer/BotPlayer
- `run(self)` — game loop:

```python
game = ConnectFour()
while not game.is_over:
    print(render_board(game.board))
    player = players[game.current_player]
    col = player.get_move(game)
    result = game.drop_token(col)
    match result:
        case MoveResult.Win(player=p, cells=cells):
            print(render_board(game.board, highlight=set(cells)))
            print(f"Player {p} wins!")
        case MoveResult.Draw():
            print(render_board(game.board))
            print("Draw!")
```

### `ui/benchmark.py` — Bot vs Bot Statistics

**`BenchmarkResult`** (dataclass):
- Overall: `bot1_wins`, `bot2_wins`, `draws`
- By starter: `bot1_wins_as_p1`, `bot1_wins_as_p2`, `bot2_wins_as_p1`,
  `bot2_wins_as_p2`, `draws_bot1_first`, `draws_bot2_first`
- `print_summary()` — formatted table with percentages

**`BenchmarkUI`**:
- `__init__(self, bot1: BotPlayer, bot2: BotPlayer)`
- `run(self, n_games=100, verbose=False) -> BenchmarkResult` — alternates who
  starts first each game.

### `__main__.py` — CLI

```
connect-four play [--p1 TYPE] [--p2 TYPE] [--difficulty 0-3]
connect-four benchmark [--p1 TYPE] [--p2 TYPE] [--n GAMES] [--difficulty 0-3] [--verbose]
```

Player types: `human`, `bot`/`perfect`, `random`, `first`

### `pyproject.toml`

- Build backend: maturin
- `tool.maturin.python-source = "src"`
- `tool.maturin.python-packages = ["connect_four"]`
- `tool.maturin.manifest-path = "src/connect_four_rs/Cargo.toml"`
- `tool.maturin.module-name = "connect_four_rs"`
- Dev deps: pytest, pytest-cov

### Cargo files

Root `Cargo.toml`: workspace with `members = ["src/connect_four_rs"]`

Crate `Cargo.toml`: `connect-four-ai = "1.0.0"`, `pyo3 = { version = "0.25",
features = ["extension-module"] }`

---

## Development Workflow

```sh
uv sync                       # create venv, install Python deps
uv run maturin develop        # compile Rust, install .so into venv
uv run pytest                 # run all tests
uv run connect-four play      # interactive game
uv run connect-four benchmark # bot benchmark
```

---

## Parallelizable Implementation Tasks

The project decomposes into **4 independent work units** that touch
non-overlapping files and can be implemented simultaneously:

### Task 1: Scaffolding + Engine (foundation)

**Files:**
- `pyproject.toml`
- `Cargo.toml` (workspace root)
- `.python-version`
- `.gitignore`
- `src/connect_four/__init__.py`
- `src/connect_four/ui/__init__.py`
- `tests/__init__.py`
- `src/connect_four/engine.py`
- `tests/test_engine.py`

**Why together:** The scaffolding is tiny and the engine is the project's
foundation — having them in one unit means this agent can immediately run
`pytest` to validate the engine.

### Task 2: Rust Extension

**Files:**
- `src/connect_four_rs/Cargo.toml`
- `src/connect_four_rs/src/lib.rs`

**Notes:** Depends only on the `connect-four-ai` crate. Can be developed and
compiled independently with `cargo build`. Uses the verified API documented
above (Position 0-based, AIPlayer, Difficulty enum).

### Task 3: Players + Bots

**Files:**
- `src/connect_four/players.py`
- `src/connect_four/bots/__init__.py`
- `src/connect_four/bots/random.py`
- `src/connect_four/bots/first_available.py`
- `src/connect_four/bots/perfect.py`
- `tests/test_players.py`
- `tests/test_bots.py`

**Notes:** Imports `engine` module. `Bot` protocol lives in `bots/__init__.py`
alongside re-exports. `PerfectBot` lazily imports `connect_four_rs` so tests
can run without compiled Rust. Tests cover RandomBot, FirstAvailableBot,
BotPlayer validation, HumanPlayer (via monkeypatched input).

### Task 4: UIs + CLI

**Files:**
- `src/connect_four/ui/terminal.py`
- `src/connect_four/ui/benchmark.py`
- `src/connect_four/__main__.py`

**Notes:** Imports engine, players, bots. TerminalUI uses ANSI colors. BenchmarkUI
alternates starting player. CLI wires everything together via argparse with
`play` and `benchmark` subcommands.

### Dependency graph

```
Task 1 (scaffolding + engine)  ──┐
Task 2 (rust extension)         ──┼── all independent, run in parallel
Task 3 (players + bots)         ──┤
Task 4 (UIs + CLI)              ──┘
```

All 4 tasks touch completely disjoint files, so they can run as parallel
subagents in isolated worktrees and be merged cleanly.

### Post-merge integration

After all 4 are merged:
1. `uv sync && uv run maturin develop` — compile everything
2. `uv run pytest` — verify all tests pass with real Rust extension
3. `uv run connect-four play --p1 human --p2 bot` — smoke test
4. `uv run connect-four benchmark --p1 bot --p2 random --n 100` — benchmark smoke test
