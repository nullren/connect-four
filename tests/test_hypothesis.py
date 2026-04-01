"""Property-based tests for connect_four.engine using Hypothesis."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from connect_four.engine import COLS, ROWS, ConnectFour, MoveResult, build_board

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def build_game(col_sequence: list[int]) -> ConnectFour:
    """Play each column in sequence, stopping at the first invalid move or game over."""
    game = ConnectFour()
    for col in col_sequence:
        if game.is_over:
            break
        game.play(col)  # invalid cols are silently ignored via MoveResult
    return game


def build_valid_game(col_sequence: list[int]) -> ConnectFour:
    """Play only valid columns from sequence, skipping invalid ones, stop when over."""
    game = ConnectFour()
    for col in col_sequence:
        if game.is_over:
            break
        if col in game.valid_moves:
            game.play(col)
    return game


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


@given(st.lists(st.integers(min_value=0, max_value=6), max_size=42))
def test_board_is_deterministic(col_sequence: list[int]) -> None:
    """build_board(moves) returns the same result on two calls."""
    game = build_valid_game(col_sequence)
    assert build_board(game.moves) == build_board(game.moves)


@given(st.lists(st.integers(min_value=0, max_value=6), max_size=42))
def test_valid_moves_empty_iff_game_over(col_sequence: list[int]) -> None:
    """valid_moves is [] iff the game is over."""
    game = build_valid_game(col_sequence)
    if game.is_over:
        assert game.valid_moves == []
    else:
        assert len(game.valid_moves) > 0


@given(st.lists(st.integers(min_value=0, max_value=6), max_size=42))
def test_current_player_alternates(col_sequence: list[int]) -> None:
    """current_player is 1 iff len(moves) is even."""
    game = build_valid_game(col_sequence)
    expected = 1 if len(game.moves) % 2 == 0 else 2
    assert game.current_player == expected


@given(st.lists(st.integers(min_value=0, max_value=6), max_size=42))
def test_board_piece_count_matches_moves(col_sequence: list[int]) -> None:
    """Total non-zero cells in board equals len(moves)."""
    game = build_valid_game(col_sequence)
    count = sum(1 for row in game.board for cell in row if cell != 0)
    assert count == len(game.moves)


@given(st.lists(st.integers(min_value=0, max_value=6), max_size=42))
def test_gravity_no_floating_pieces(col_sequence: list[int]) -> None:
    """If board[r][c] is non-zero, board[r-1][c] must also be non-zero."""
    game = build_valid_game(col_sequence)
    board = game.board
    for r in range(1, ROWS):
        for c in range(COLS):
            if board[r][c] != 0:
                assert board[r - 1][c] != 0, f"Floating piece at row={r}, col={c}"


@given(st.lists(st.integers(min_value=0, max_value=6), max_size=42))
def test_only_last_player_can_win(col_sequence: list[int]) -> None:
    """If there is a winner, it must be the player who made the last move."""
    game = build_valid_game(col_sequence)
    if game.winner is not None and len(game.moves) > 0:
        # The last mover is the player *before* current_player
        last_mover = 1 if len(game.moves) % 2 == 1 else 2
        assert game.winner == last_mover


@given(st.lists(st.integers(min_value=0, max_value=6), max_size=42))
def test_winner_implies_game_over(col_sequence: list[int]) -> None:
    """If winner is not None, is_over must be True."""
    game = build_valid_game(col_sequence)
    if game.winner is not None:
        assert game.is_over


@given(st.lists(st.integers(min_value=0, max_value=6), max_size=42))
def test_play_valid_column_adds_one_piece(col_sequence: list[int]) -> None:
    """Playing a valid column always adds exactly one piece to the board."""
    game = build_valid_game(col_sequence)
    if game.is_over:
        return
    col = game.valid_moves[0]
    before = sum(1 for row in game.board for cell in row if cell != 0)
    game.play(col)
    after = sum(1 for row in game.board for cell in row if cell != 0)
    assert after == before + 1


@given(st.lists(st.integers(min_value=0, max_value=6), max_size=42))
def test_play_invalid_column_does_not_change_state(col_sequence: list[int]) -> None:
    """Playing an out-of-range column returns InvalidMove and leaves state unchanged."""
    game = build_valid_game(col_sequence)
    moves_before = game.moves
    result = game.play(7)  # always out of range
    assert isinstance(result, MoveResult.InvalidMove)
    assert game.moves == moves_before


@given(st.lists(st.integers(min_value=0, max_value=6), max_size=42))
@settings(max_examples=200)
def test_play_on_finished_game_is_invalid(col_sequence: list[int]) -> None:
    """Any move on a finished game returns InvalidMove."""
    game = build_valid_game(col_sequence)
    if not game.is_over:
        return
    for col in range(COLS):
        result = game.play(col)
        assert isinstance(result, MoveResult.InvalidMove)
