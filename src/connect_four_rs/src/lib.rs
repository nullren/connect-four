use connect_four_ai::{AIPlayer, Difficulty, Position};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

fn build_position(moves: &[i64]) -> PyResult<Position> {
    let mut pos = Position::new();
    for (i, &col) in moves.iter().enumerate() {
        if col < 0 || col >= Position::WIDTH as i64 {
            return Err(PyValueError::new_err(format!(
                "Move {i}: column {col} out of range 0..{}",
                Position::WIDTH
            )));
        }
        let col = col as usize;
        if pos.is_won_position() {
            return Err(PyValueError::new_err(format!(
                "Move {i}: game is already won"
            )));
        }
        if !pos.is_playable(col) {
            return Err(PyValueError::new_err(format!(
                "Move {i}: column {col} is full"
            )));
        }
        pos.play(col);
    }
    Ok(pos)
}

fn map_difficulty(difficulty: u8) -> PyResult<Difficulty> {
    match difficulty {
        0 => Ok(Difficulty::Easy),
        1 => Ok(Difficulty::Medium),
        2 => Ok(Difficulty::Hard),
        3 => Ok(Difficulty::Impossible),
        _ => Err(PyValueError::new_err(format!(
            "Invalid difficulty {difficulty}: must be 0 (Easy), 1 (Medium), 2 (Hard), or 3 (Impossible)"
        ))),
    }
}

#[pyfunction]
fn best_move(moves: Vec<i64>, difficulty: u8) -> PyResult<Option<usize>> {
    let pos = build_position(&moves)?;
    if pos.is_won_position() {
        return Ok(None);
    }
    let difficulty = map_difficulty(difficulty)?;
    let mut player = AIPlayer::new(difficulty);
    Ok(player.get_move(&pos))
}

#[pyfunction]
fn all_move_scores(moves: Vec<i64>) -> PyResult<Vec<Option<i8>>> {
    let pos = build_position(&moves)?;
    if pos.is_won_position() {
        return Ok(vec![None; Position::WIDTH]);
    }
    let mut player = AIPlayer::new(Difficulty::Impossible);
    let scores = player.get_all_move_scores(&pos);
    Ok(scores.to_vec())
}

#[pymodule]
fn connect_four_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(best_move, m)?)?;
    m.add_function(wrap_pyfunction!(all_move_scores, m)?)?;
    Ok(())
}
