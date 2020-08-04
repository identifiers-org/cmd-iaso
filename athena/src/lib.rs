//! `athena` is a Python module implemented in Rust which decorates
//! the `metis` crate.
//!
//! It implements a Generalised Suffix Tree which can compute the
//! shared fragments of its input text fragments.
//!
//! # Examples
//!
//! ```python
//! from athena import SharedFragmentTree
//!
//! tree = SharedFragmentTree([
//!     ("a", "b", "c", "d", "e"),
//!     ("a", "b", "c"),
//!     ("c", "d", "e"),
//!     ("b", "c")
//! ])
//!
//! assert generate_tree().extract_longest_common_non_overlapping_fragments(
//!     {0}, {1, 2, 3}
//! ) == [(["c", "d", "e"], 2), (["a", "b"], 0)]
//! ```

#![deny(clippy::all)]
#![deny(missing_docs)]

use pyo3::prelude::*;

mod shared_fragment_tree;
pub use shared_fragment_tree::SharedFragmentTree;

#[cfg(test)]
mod tests;

/// `athena` is a Python module implemented in Rust which decorates
/// the `metis` crate.
///
/// It implements a Generalised Suffix Tree which can compute the
/// shared fragments of its input text fragments.
///
/// Use `help(athena)` to look at the documentation of the module.
#[pymodule]
pub fn athena(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<SharedFragmentTree>()?;

    Ok(())
}
