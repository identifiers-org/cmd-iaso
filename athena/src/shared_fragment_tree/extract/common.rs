use pyo3::prelude::*;

use metis::all_any_set::AllAnySet;

use bit_set::BitSet;
use std::iter::FromIterator;

use super::SharedFragmentTree;

#[pymethods]
impl SharedFragmentTree {
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
                BitSet::from_iter(all.into_iter()),
                BitSet::from_iter(any.into_iter()),
            ) {
                Some(string_indices) => string_indices,
                None => {
                    return Err(PyErr::new::<pyo3::exceptions::ValueError, _>(
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
