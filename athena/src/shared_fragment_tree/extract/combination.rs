use pyo3::prelude::*;

use metis::{all_any_set::AllAnySet, word_string::WordString};

use bit_set::BitSet;
use std::iter::FromIterator;

use super::SharedFragmentTree;

fn common_early_stop(fraction: f64, fragments: &mut Vec<(WordString, usize)>) -> bool {
    // Number of words in the largest fragment
    let max_lcs_len = fragments[0].0.len() as f64;
    // Number of words in the latest fragment
    let cur_lcs_len = fragments[fragments.len() - 1].0.len() as f64;

    // Iff the latest fragment is only a fraction of the size of the largest one, stop
    // early and discard the latest fragment
    if cur_lcs_len <= (max_lcs_len * fraction) {
        fragments.pop();

        true
    } else {
        false
    }
}

#[pymethods]
impl SharedFragmentTree {
    #[args(
        fraction = "1.0f64 / 100.0f64",
        combinator = r#""NOISE""#,
        debug = "false"
    )]
    pub fn extract_combination_of_all_common_fragments(
        &self,
        py: Python,
        fraction: f64,
        combinator: &str,
        debug: bool,
    ) -> PyResult<Vec<String>> {
        py.allow_threads(|| {
            let string_indices =
                match AllAnySet::new(BitSet::from_iter(0..self.tree.len()), BitSet::new()) {
                    Some(string_indices) => string_indices,
                    None => {
                        return Err(PyErr::new::<pyo3::exceptions::ValueError, _>(
                            "SharedFragmentTree is empty",
                        ))
                    }
                };

            let mut fragments = self.tree.extract_longest_common_non_overlapping_substrings(
                string_indices,
                Some(&mut |#[allow(non_snake_case)] _L: usize,
                           fragments: &mut Vec<(WordString, usize)>| {
                    common_early_stop(fraction, fragments)
                }),
                debug,
            );

            fragments.sort_unstable_by_key(|(_, start)| *start);

            let mut combined_fragments: Vec<String> = Vec::new();

            for (fragment, _start) in fragments.into_iter() {
                combined_fragments.extend(fragment.into_iter());
                combined_fragments.push(combinator.to_owned());
            }

            combined_fragments.pop();

            Ok(combined_fragments)
        })
    }
}
