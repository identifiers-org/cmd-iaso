//! `athena` is a Python module implemented in Rust which decorates
//! the `metis` crate.
//!
//! It implements a tokeniser helper function which works on HTML,
//! XML, JSON and raw text documents.
//!
//! It also implements a Generalised Suffix Tree which can compute
//! the shared fragments of its input text fragments.
//!
//! # Examples
//!
//! ```python
//! from athena import tokenise_and_join_with_spaces
//!
//! joined_tokens = tokenise_and_join_with_spaces("""
//! <html>
//!   <ul>
//!     <li>A</li>
//!     <li>b</li>
//!     <li>
//!       <a href="https://github.com/identifiers-org/cmd-iaso">c</a>
//!     </li>
//!     <li>D</li>
//!     <li>ignore</li>
//!     <li>E</li>
//!   </ul>
//! </html>
//! """, ["ignore"])
//!
//! assert joined_tokens == "a b c d e"
//! ```
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
use pyo3::wrap_pyfunction;

mod tokeniser;

mod shared_fragment_tree;
pub use shared_fragment_tree::SharedFragmentTree;

#[cfg(test)]
mod tests;

/// Tokenises the `content` string and joins the tokens in lower case with spaces.
/// * If the `content` is an HTML, XML or JSON document, only the human-readable
/// text will be extracted.
/// * Any URLs contained within the `content` will be removed before tokenisation.
/// * Any strings contained in `exclusions` will be removed from the `content`.
#[pyfunction(module = "athena")]
#[text_signature = "(content, exclusions, /)"]
pub fn tokenise_and_join_with_spaces(content: &str, exclusions: Vec<&str>) -> String {
    tokeniser::tokenise_and_join_with_spaces(content.as_bytes(), &exclusions)
}

/// `athena` is a Python module implemented in Rust which decorates
/// the `metis` crate.
///
/// It implements a tokeniser helper function which works on HTML,
/// XML, JSON and raw text documents.
///
/// It also implements a Generalised Suffix Tree which can compute
/// the shared fragments of its input text fragments.
///
/// Use `help(athena)` to look at the documentation of the module.
#[pymodule]
fn athena(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(tokenise_and_join_with_spaces))?;
    m.add_class::<SharedFragmentTree>()?;

    Ok(())
}
