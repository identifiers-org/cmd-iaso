use pyo3::prelude::*;

use metis::{AllAnySet, FrozenVecSet};

use std::iter::FromIterator;

use super::SharedFragmentTree;

#[pymethods]
impl SharedFragmentTree {
    /// Extracts all common text fragments in the tree. The output will be
    /// ordered decreasingly by substring length. For each substring, it will
    /// also report its start index the `input` string at the first index in
    /// `all`.
    ///
    /// This method can be executed on multiple threads in parallel as it
    /// releases the Python GIL `py`.
    ///
    /// `all` specifies the set of indices of strings from `input` from which
    /// all must contain the fragment. The method will return an error iff `all`
    /// is empty.
    ///
    /// `any` specifies the set of indices of strings from `input` from which
    /// at least one must contain the fragment. If `any` is empty, it will be
    /// ignored and have no effect.
    ///
    /// Iff `debug` is `true`, the state of extraction will be printed after each
    /// iteration.
    #[text_signature = "($self, all, any, /, debug=False)"]
    #[args(debug = "false")]
    pub fn extract_longest_common_non_overlapping_fragments(
        &self,
        py: Python,
        all: std::collections::HashSet<usize>,
        any: std::collections::HashSet<usize>,
        debug: bool,
    ) -> PyResult<Vec<(Vec<String>, usize)>> {
        py.allow_threads(|| {
            let string_indices = match AllAnySet::new(
                FrozenVecSet::from_iter(all.into_iter()),
                FrozenVecSet::from_iter(any.into_iter()),
            ) {
                Some(string_indices) => string_indices,
                None => {
                    return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                        "all set is empty",
                    ))
                }
            };

            Ok(self
                .tree
                .extract_longest_common_non_overlapping_substrings(string_indices, None, debug)
                .into_iter()
                .map(|(word_string, start)| (word_string.into(), start))
                .collect())
        })
    }
}
