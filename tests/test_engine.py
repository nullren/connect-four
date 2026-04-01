"""Comprehensive tests for connect_four.engine."""

from __future__ import annotations

import pytest

from connect_four.engine import (
    COLS,
    MAX_MOVES,
    ROWS,
    ConnectFour,
    MoveResult,
    build_board,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def play_moves(cols: list[int]) -> ConnectFour:
    """Create a game and play a sequence of moves, returning the game."""
    game = ConnectFour()
    for c in cols:
        game.play(c)
    return game


# ---------------------------------------------------------------------------
# Empty board
# ---------------------------------------------------------------------------


class TestEmptyBoard:
    def test_board_is_all_zeros(self) -> None:
        game = ConnectFour()
        board = game.board
        assert len(board) == ROWS
        assert all(len(row) == COLS for row in board)
        assert all(cell == 0 for row in board for cell in row)

    def test_current_player_is_1(self) -> None:
        assert ConnectFour().current_player == 1

    def test_valid_moves_all_columns(self) -> None:
        assert ConnectFour().valid_moves == list(range(COLS))

    def test_not_over(self) -> None:
        assert not ConnectFour().is_over

    def test_no_winner(self) -> None:
        assert ConnectFour().winner is None

    def test_moves_empty(self) -> None:
        assert ConnectFour().moves == ()


# ---------------------------------------------------------------------------
# Single move
# ---------------------------------------------------------------------------


class TestSingleMove:
    def test_places_at_bottom(self) -> None:
        game = ConnectFour()
        game.play(3)
        assert game.board[0][3] == 1

    def test_returns_ongoing(self) -> None:
        result = ConnectFour().play(3)
        assert isinstance(result, MoveResult.Ongoing)
        assert result.player == 2

    def test_current_player_switches(self) -> None:
        game = ConnectFour()
        game.play(0)
        assert game.current_player == 2


# ---------------------------------------------------------------------------
# Alternating players
# ---------------------------------------------------------------------------


class TestAlternatingPlayers:
    def test_two_moves_different_columns(self) -> None:
        game = play_moves([0, 1])
        assert game.board[0][0] == 1
        assert game.board[0][1] == 2
        assert game.current_player == 1

    def test_two_moves_same_column(self) -> None:
        game = play_moves([3, 3])
        assert game.board[0][3] == 1
        assert game.board[1][3] == 2

    def test_current_player_alternates(self) -> None:
        game = ConnectFour()
        for i in range(6):
            assert game.current_player == (i % 2) + 1
            game.play(i)


# ---------------------------------------------------------------------------
# Invalid moves
# ---------------------------------------------------------------------------


class TestColumnOverflow:
    def test_returns_invalid_move(self) -> None:
        game = ConnectFour()
        for _ in range(ROWS):
            game.play(0)
        result = game.play(0)
        assert isinstance(result, MoveResult.InvalidMove)
        assert "full" in result.reason

    def test_does_not_change_state(self) -> None:
        game = ConnectFour()
        for _ in range(ROWS):
            game.play(0)
        moves_before = game.moves
        game.play(0)
        assert game.moves == moves_before


class TestOutOfRange:
    def test_negative_column(self) -> None:
        result = ConnectFour().play(-1)
        assert isinstance(result, MoveResult.InvalidMove)
        assert "out of range" in result.reason

    def test_too_large_column(self) -> None:
        result = ConnectFour().play(COLS)
        assert isinstance(result, MoveResult.InvalidMove)
        assert "out of range" in result.reason

    def test_way_too_large(self) -> None:
        result = ConnectFour().play(100)
        assert isinstance(result, MoveResult.InvalidMove)


class TestDropAfterGameOver:
    def test_returns_invalid_after_win(self) -> None:
        # P1 wins horizontally on row 0.
        game = play_moves([0, 0, 1, 1, 2, 2])
        result = game.play(3)  # P1 wins
        assert isinstance(result, MoveResult.Win)
        result2 = game.play(4)
        assert isinstance(result2, MoveResult.InvalidMove)
        assert "over" in result2.reason


# ---------------------------------------------------------------------------
# Horizontal win
# ---------------------------------------------------------------------------


class TestHorizontalWin:
    def test_player1_wins(self) -> None:
        # P1: 0,1,2,3  P2: 0,1,2 (stacking on same cols for P2 filler)
        # Simpler: P1 plays cols 0-3 on row 0, P2 plays col 6 each time.
        game = ConnectFour()
        moves = [0, 6, 1, 6, 2, 6]
        for m in moves:
            game.play(m)
        result = game.play(3)  # P1 completes row 0: cols 0,1,2,3
        assert isinstance(result, MoveResult.Win)
        assert result.player == 1
        assert set(result.cells) == {(0, 0), (0, 1), (0, 2), (0, 3)}

    def test_player2_wins(self) -> None:
        game = ConnectFour()
        # P2 plays cols 0-3 on row 0, P1 plays col 6.
        moves = [6, 0, 6, 1, 6, 2, 5]
        for m in moves:
            game.play(m)
        result = game.play(3)  # P2 completes row 0: cols 0,1,2,3
        assert isinstance(result, MoveResult.Win)
        assert result.player == 2


# ---------------------------------------------------------------------------
# Vertical win
# ---------------------------------------------------------------------------


class TestVerticalWin:
    def test_four_in_a_column(self) -> None:
        # P1 stacks on col 0, P2 on col 1.
        game = ConnectFour()
        moves = [0, 1, 0, 1, 0, 1]
        for m in moves:
            game.play(m)
        result = game.play(0)  # P1: rows 0-3 in col 0
        assert isinstance(result, MoveResult.Win)
        assert result.player == 1
        assert set(result.cells) == {(0, 0), (1, 0), (2, 0), (3, 0)}


# ---------------------------------------------------------------------------
# Diagonal wins
# ---------------------------------------------------------------------------


class TestDiagonalWinUp:
    """Diagonal going up-right: /"""

    def test_slash_diagonal(self) -> None:
        # Build a / diagonal for P1 at (0,0),(1,1),(2,2),(3,3).
        game = ConnectFour()
        # col 0: P1
        # col 1: P2, P1
        # col 2: P2, P1 (need filler), P1... tricky, let's be precise.
        #
        # We need:
        #   (0,0)=1, (1,1)=1, (2,2)=1, (3,3)=1
        # Column 0: 1 piece (P1)
        # Column 1: row0=P2, row1=P1
        # Column 2: row0=?, row1=?, row2=P1
        # Column 3: row0=?, row1=?, row2=?, row3=P1
        moves = [
            0,  # P1 at (0,0)
            1,  # P2 at (0,1)
            1,  # P1 at (1,1)
            2,  # P2 at (0,2)
            2,  # P1 at (1,2)
            3,  # P2 at (0,3)
            2,  # P1 at (2,2)
            3,  # P2 at (1,3)
            3,  # P1 at (2,3)
            6,  # P2 filler
            3,  # P1 at (3,3) — win!
        ]
        for m in moves[:-1]:
            game.play(m)
        result = game.play(moves[-1])
        assert isinstance(result, MoveResult.Win)
        assert result.player == 1
        assert set(result.cells) == {(0, 0), (1, 1), (2, 2), (3, 3)}


class TestDiagonalWinDown:
    r"""Diagonal going up-left: \\"""

    def test_backslash_diagonal(self) -> None:
        # Build a \ diagonal for P1 at (3,0),(2,1),(1,2),(0,3).
        game = ConnectFour()
        moves = [
            3,  # P1 at (0,3)
            2,  # P2 at (0,2)
            2,  # P1 at (1,2)
            1,  # P2 at (0,1)
            1,  # P1 at (1,1)
            0,  # P2 at (0,0)
            1,  # P1 at (2,1)
            0,  # P2 at (1,0)
            0,  # P1 at (2,0)
            6,  # P2 filler
            0,  # P1 at (3,0) — win!
        ]
        for m in moves[:-1]:
            game.play(m)
        result = game.play(moves[-1])
        assert isinstance(result, MoveResult.Win)
        assert result.player == 1
        assert set(result.cells) == {(3, 0), (2, 1), (1, 2), (0, 3)}


# ---------------------------------------------------------------------------
# Draw
# ---------------------------------------------------------------------------


class TestDraw:
    def test_full_board_no_winner(self) -> None:
        # A carefully constructed 42-move draw.
        # Fill columns in a pattern that avoids four-in-a-row.
        # Pattern: fill each column bottom-up, alternating in a way that
        # prevents wins.
        #
        # Using a known draw sequence (0-based columns):
        draw_moves = [
            0, 1, 0, 1, 0, 1,  # col 0: 1,1,1 col 1: 2,2,2 (3 each)
            1, 0, 1, 0, 1, 0,  # col 0: 2,2,2 col 1: 1,1,1 (full both)
            2, 3, 2, 3, 2, 3,  # col 2: 1,1,1 col 3: 2,2,2
            3, 2, 3, 2, 3, 2,  # col 2: 2,2,2 col 3: 1,1,1 (full both)
            4, 5, 4, 5, 4, 5,  # col 4: 1,1,1 col 5: 2,2,2
            5, 4, 5, 4, 5, 4,  # col 4: 2,2,2 col 5: 1,1,1 (full both)
            6, 6, 6, 6, 6, 6,  # col 6: 1,2,1,2,1,2
        ]
        game = ConnectFour()
        result = None
        for m in draw_moves:
            result = game.play(m)
        assert isinstance(result, MoveResult.Draw)
        assert game.is_over
        assert game.winner is None
        assert len(game.moves) == MAX_MOVES
        assert game.valid_moves == []


# ---------------------------------------------------------------------------
# Undo
# ---------------------------------------------------------------------------


class TestUndo:
    def test_undo_single_move(self) -> None:
        game = ConnectFour()
        game.play(3)
        game.undo()
        assert game.moves == ()
        assert game.board[0][3] == 0
        assert game.current_player == 1

    def test_undo_empty_raises(self) -> None:
        with pytest.raises(IndexError):
            ConnectFour().undo()

    def test_undo_then_replay(self) -> None:
        game = ConnectFour()
        game.play(0)
        game.play(1)
        game.undo()
        # Should be P2's turn again.
        assert game.current_player == 2
        result = game.play(2)
        assert isinstance(result, MoveResult.Ongoing)
        assert game.board[0][2] == 2

    def test_undo_win_allows_more_play(self) -> None:
        game = ConnectFour()
        moves = [0, 6, 1, 6, 2, 6, 3]  # P1 wins horizontally
        for m in moves:
            game.play(m)
        assert game.is_over
        game.undo()
        assert not game.is_over
        assert game.winner is None
        # Can still play.
        result = game.play(4)
        assert isinstance(result, MoveResult.Ongoing)


# ---------------------------------------------------------------------------
# valid_moves
# ---------------------------------------------------------------------------


class TestValidMoves:
    def test_full_column_excluded(self) -> None:
        game = ConnectFour()
        # Fill column 3.
        for i in range(ROWS):
            game.play(3)
            if i < ROWS - 1:
                game.play(6)  # filler to alternate
        assert 3 not in game.valid_moves

    def test_empty_board(self) -> None:
        assert ConnectFour().valid_moves == list(range(COLS))


# ---------------------------------------------------------------------------
# current_player
# ---------------------------------------------------------------------------


class TestCurrentPlayer:
    def test_alternates(self) -> None:
        game = ConnectFour()
        for i in range(7):
            expected = (i % 2) + 1
            assert game.current_player == expected
            game.play(i)


# ---------------------------------------------------------------------------
# build_board standalone
# ---------------------------------------------------------------------------


class TestBuildBoard:
    def test_empty(self) -> None:
        board = build_board([])
        assert all(cell == 0 for row in board for cell in row)

    def test_single_move(self) -> None:
        board = build_board([4])
        assert board[0][4] == 1

    def test_stacking(self) -> None:
        board = build_board([2, 2, 2])
        assert board[0][2] == 1
        assert board[1][2] == 2
        assert board[2][2] == 1

    def test_matches_game_board(self) -> None:
        moves = [0, 1, 2, 3, 0, 1, 2, 3]
        game = play_moves(moves)
        assert build_board(moves) == game.board


# ---------------------------------------------------------------------------
# moves property is read-only
# ---------------------------------------------------------------------------


class TestMovesReadOnly:
    def test_returns_tuple(self) -> None:
        game = ConnectFour()
        game.play(3)
        m = game.moves
        assert isinstance(m, tuple)

    def test_mutation_does_not_affect_game(self) -> None:
        game = ConnectFour()
        game.play(3)
        m = game.moves
        # Tuples are immutable, so we can't mutate — that's the point.
        assert m == (3,)
        # Accessing again should still be the same.
        assert game.moves == (3,)


# ---------------------------------------------------------------------------
# MoveResult pattern matching
# ---------------------------------------------------------------------------


class TestMoveResultPatternMatching:
    def test_ongoing_match(self) -> None:
        result = ConnectFour().play(0)
        match result:
            case MoveResult.Ongoing(player=p):
                assert p == 2
            case _:
                pytest.fail("Expected Ongoing")

    def test_win_match(self) -> None:
        game = ConnectFour()
        for m in [0, 6, 1, 6, 2, 6]:
            game.play(m)
        result = game.play(3)
        match result:
            case MoveResult.Win(player=p, cells=c):
                assert p == 1
                assert len(c) == 4
            case _:
                pytest.fail("Expected Win")

    def test_draw_match(self) -> None:
        draw_moves = [
            0, 1, 0, 1, 0, 1,
            1, 0, 1, 0, 1, 0,
            2, 3, 2, 3, 2, 3,
            3, 2, 3, 2, 3, 2,
            4, 5, 4, 5, 4, 5,
            5, 4, 5, 4, 5, 4,
            6, 6, 6, 6, 6, 6,
        ]
        game = ConnectFour()
        result = None
        for m in draw_moves:
            result = game.play(m)
        match result:
            case MoveResult.Draw():
                pass  # success
            case _:
                pytest.fail("Expected Draw")

    def test_invalid_match(self) -> None:
        result = ConnectFour().play(-1)
        match result:
            case MoveResult.InvalidMove(reason=r):
                assert "out of range" in r
            case _:
                pytest.fail("Expected InvalidMove")
