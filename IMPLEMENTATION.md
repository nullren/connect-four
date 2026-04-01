# Connect Four — Implementation Notes

## Architecture

```
connect-four/
├── src/
│   ├── connect_four/            # Python package
│   │   ├── engine.py            # Pure game logic
│   │   ├── players.py           # HumanPlayer, BotPlayer, UndoRequested, QuitRequested
│   │   ├── bots/
│   │   │   ├── __init__.py      # Bot protocol + auto-discovery registry
│   │   │   ├── random.py
│   │   │   ├── first_available.py
│   │   │   ├── minimax.py
│   │   │   ├── mcts.py
│   │   │   └── perfect.py       # Rust-backed perfect play
│   │   ├── ui/
│   │   │   ├── terminal.py      # Interactive ANSI terminal UI
│   │   │   └── benchmark.py     # Bot-vs-bot statistics
│   │   └── __main__.py          # CLI entry point (argparse)
│   └── connect_four_rs/         # Rust crate (PyO3 bindings)
│       └── src/lib.rs
└── tests/
    ├── test_engine.py
    ├── test_players.py
    ├── test_bots.py
    └── test_hypothesis.py       # Property-based tests (Hypothesis)
```

## Key Design Decisions

### Move history as the only state

`ConnectFour` stores a single `list[int]` of 0-based column indices. Everything
else — board grid, winner, valid moves, current player — is derived on demand.
This makes undo trivial (pop the list), replay free (replay from any prefix),
and passing state to bots cheap (just the list).

```python
game = ConnectFour()
result = game.play(3)   # MoveResult.Ongoing | .Win | .Draw | .InvalidMove
game.undo()
board = game.board      # derived tuple[tuple[int, ...], ...] — immutable
```

### MoveResult discriminated union

`play()` never raises on bad input. All outcomes are explicit variants:

```python
match game.play(col):
    case MoveResult.Win(player=p, cells=cells):   ...
    case MoveResult.Draw():                        ...
    case MoveResult.Ongoing(player=p):             ...
    case MoveResult.InvalidMove(reason=r):         ...
```

### Immutable Board type

`Board = tuple[tuple[int, ...], ...]` — immutable and hashable. This lets the
minimax transposition cache use boards directly as dict keys with no extra
work. `build_board(moves)` is a public standalone utility for bots that need a
grid view without constructing a full `ConnectFour`.

### Player enum

`Player(IntEnum)` with `ONE = 1`, `TWO = 2`. Inheriting from `int` keeps all
`== 1` / `== 2` comparisons working without changes throughout the codebase.

### Bot protocol and auto-discovery registry

```python
class Bot(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def description(self) -> str: ...
    def next_move(self, moves: Sequence[int]) -> int: ...
```

Each bot file calls `register(BotInstance())` at module level. `bots/__init__.py`
discovers and imports all sibling modules via `pkgutil.iter_modules`, so adding
a new bot requires only a new file — no changes to `__init__.py` or the CLI.

Bots receive `Sequence[int]` (read-only move history), not the full engine
object. This is the minimal complete interface: the column sequence is enough
to derive any board state, and keeping the interface narrow means bots stay
decoupled from the engine's internals.

### MinimaxBot

Alpha-beta pruning with several practical improvements:

- **Center-first move ordering** (`3, 2, 4, 1, 5, 0, 6`) dramatically improves
  pruning because center columns lead to more wins.
- **play/undo traversal** on a single shared `ConnectFour` instance rather than
  creating new objects per node — avoids O(nodes) allocations.
- **Transposition cache** keyed on the immutable `Board` type. Cached entries
  store `(score, depth)` so a shallow result is replaced if a deeper search
  visits the same position.

Default search depth is 6 half-moves (3 full moves per side).

### MCTSBot

Four-phase Monte Carlo Tree Search:

1. **Select** — descend the tree by UCB1 score until a node with unexplored
   children is found.
2. **Expand** — add one random unexplored child.
3. **Rollout** — play randomly to a terminal state; return `1.0` (P1 wins),
   `-1.0` (P2 wins), or `None` (draw).
4. **Backpropagate** — walk to root, incrementing visits; credit a win to each
   node whose mover matches the result. Mover is determined by
   `len(node.moves) % 2`: odd → Player 1 moved last.

Move selection uses the "robust child" criterion (most visits), which is more
stable than win rate alone. Default is 300 simulations per move.

### PerfectBot (Rust)

Wraps the [`connect-four-ai`](https://crates.io/crates/connect-four-ai) crate
via PyO3. The Rust layer exposes two functions:

```python
best_move(moves: list[int], difficulty: int) -> int | None
all_move_scores(moves: list[int]) -> list[int | None]
```

`difficulty` maps to `Easy/Medium/Hard/Impossible` (0–3). The Rust extension
is lazily imported inside `PerfectBot.next_move()` so the package remains
importable even without the compiled `.so`.

### Terminal UI

The board renders using Unicode box-drawing characters (`┌┬┐`, `├┼┤`, `└┴┘`)
with a full grid of column dividers. Column numbers sit above the top border to
suggest dropping pieces from above. Player 1 pieces are red, Player 2 yellow,
winning cells cyan.

The board redraws in-place using ANSI cursor-up (`\033[nF`) + clear-to-end
(`\033[J`) rather than scrolling, so the display stays fixed on screen.

Player input uses exception-based signalling:
- `UndoRequested` — raised by `HumanPlayer` on `u`; caught by `TerminalUI`,
  which undoes the last 2 moves so the human returns to their own turn
- `QuitRequested` — raised on `q`, Ctrl-C, or Ctrl-D; caught at the top of
  the run loop for a clean exit

Think time is tracked per player with `time.perf_counter()` and printed as a
summary when the game ends.

### Benchmark UI

Alternates which bot goes first each game. Reports win/loss/draw broken down
by who started. Tracks think time with `time.perf_counter()` around each
`get_move()` call and prints total and average ms/move per bot.

### Docker

Multi-stage build with three distinct cached layers in the builder stage:

1. **Rust dep fetch** — `cargo fetch` with a stub `lib.rs`; invalidated only
   when `Cargo.lock` changes.
2. **Rust compilation** — `maturin build --release` with a stub Python package;
   invalidated only when Rust source changes.
3. **Python packaging** — copies real Python source and re-runs
   `maturin build`; cargo finds its `target/` cache intact and skips
   recompilation, so this layer is fast.

The runtime stage is a slim Python image with no Rust toolchain — just the
pre-built wheel installed.

## Testing

- `test_engine.py` — unit tests for all `ConnectFour` and `MoveResult` behaviour
- `test_players.py` — `BotPlayer` validation (invalid columns, game-over guard)
- `test_bots.py` — smoke tests for each registered bot
- `test_hypothesis.py` — 10 property-based tests via Hypothesis: gravity,
  piece counts, player alternation, only-last-mover-can-win, `valid_moves` ↔
  `is_over` consistency, play/undo invariants, and more
