use pyo3::import_exception;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use rayon::prelude::*;

use metis::{AllAnySet, OneShotGeneralisedSuffixTree, WordString};

use bincode;
use bit_set::BitSet;
use rand::{
    self,
    distributions::{DistIter, Distribution, Uniform},
    rngs::ThreadRng,
    Rng,
};
use std::iter::FromIterator;

mod packing;

import_exception!(pickle, PicklingError);
import_exception!(pickle, UnpicklingError);

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

fn shared_early_stop<D: Distribution<f64>, R: Rng>(
    rng_iter: &mut DistIter<D, R, f64>,
    threshold: f64,
    #[allow(non_snake_case)] L: usize,
    fragments: &mut Vec<(WordString, usize)>,
) -> bool {
    // Upper-bound threshold of unique information where a response is considered to
    // contain not enough unique information
    let threshold = threshold;

    // Number of words in the input document
    #[allow(non_snake_case)]
    let L = L as f64;
    // Number of words which have already been matched in shared fragments
    #[allow(non_snake_case)]
    let C = fragments
        .iter()
        .map(|(fragment, _)| fragment.len())
        .sum::<usize>() as f64;
    // Number of fragments found so far
    let n = fragments.len() as f64;
    // Number of words in the latest fragment, i.e. the maximum fragment size possible
    // for the rest of the document
    let f_n = fragments[fragments.len() - 1].0.len() as f64;
    // Measure of unique information (not shared) in the document, in range 0% - 100%
    let min_unique_information = (n + f64::ceil((L - C) / f_n) - 1.0f64) / L;
    let max_unique_information = (L - C + n - 1.0f64) / L;

    // Russian Roulette probability of stopping early
    let p = f64::sqrt(f64::max(
        f64::max(
            (min_unique_information - threshold) / (1.0f64 - threshold),
            (threshold - max_unique_information) / threshold,
        ),
        0.0f64,
    ));

    // Stop early iff (the minimum possible unique information is greater than the
    // threshold or the maximum possible unique information is less than the threshold)
    // and Russian Roulette has fired
    rng_iter.next().unwrap_or(0.0f64) < p
}

fn extract_all_shared_fragments_impl(
    tree: &OneShotGeneralisedSuffixTree,
    threshold: Option<f64>,
    debug: bool,
    rng: &mut ThreadRng,
    i: usize,
) -> Vec<Vec<String>> {
    let string_indices: AllAnySet = AllAnySet::new(
        BitSet::from_iter(i..=i),
        BitSet::from_iter((0..i).chain((i + 1)..tree.len())),
    )
    .unwrap(); // cannot fail as all set will always be {i}

    let fragments = if let Some(threshold) = threshold {
        let dist = Uniform::from(0.0f64..1.0f64);
        let mut rng_iter = dist.sample_iter(rng);

        tree.extract_longest_common_non_overlapping_substrings(
            string_indices,
            Some(&mut |#[allow(non_snake_case)] L: usize,
                       fragments: &mut Vec<(WordString, usize)>| {
                shared_early_stop(&mut rng_iter, threshold, L, fragments)
            }),
            debug,
        )
    } else {
        tree.extract_longest_common_non_overlapping_substrings(string_indices, None, debug)
    };

    fragments
        .into_iter()
        .map(|(fragments, _start)| fragments.into())
        .collect()
}

#[pyclass(module = "athena")]
pub struct SharedFragmentTree {
    tree: OneShotGeneralisedSuffixTree,
}

#[pyproto]
impl pyo3::PyObjectProtocol for SharedFragmentTree {
    fn __str__(&self) -> PyResult<String> {
        Ok(format!("{:?}", self.tree))
    }
}

#[pyproto]
impl pyo3::PySequenceProtocol for SharedFragmentTree {
    fn __len__(&self) -> usize {
        self.tree.len()
    }
}

#[pymethods]
impl SharedFragmentTree {
    #[new]
    #[args(input = "vec![]")]
    pub fn new(input: Vec<Vec<String>>) -> Self {
        SharedFragmentTree {
            tree: OneShotGeneralisedSuffixTree::new(
                input
                    .into_iter()
                    .map(|words| WordString::from(words))
                    .collect(),
            ),
        }
    }

    pub fn __setstate__(&mut self, _py: Python, state: &PyBytes) -> PyResult<()> {
        self.tree = match bincode::deserialize(&packing::unpack(state.as_bytes())) {
            Ok(tree) => tree,
            Err(e) => return Err(PyErr::new::<UnpicklingError, _>(format!("{}", e))),
        };

        Ok(())
    }

    pub fn __getstate__(&self, py: Python) -> PyResult<PyObject> {
        match bincode::serialize(&self.tree) {
            Ok(bytes) => Ok(PyBytes::new(py, &packing::pack(bytes)).to_object(py)),
            Err(e) => Err(PyErr::new::<PicklingError, _>(format!("{}", e))),
        }
    }

    pub fn size(&self) -> usize {
        self.tree.size()
    }

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

    #[args(threshold = "0.1f64", progress = "None", debug = "false")]
    pub fn extract_all_shared_fragments_for_all_strings_parallel(
        &self,
        threshold: Option<f64>,
        progress: Option<&PyAny>,
        debug: bool,
    ) -> Vec<Vec<Vec<String>>> {
        // rayon takes care of internal parallelisation already, no need to release GIL

        // Unsafe Send + Pointer required as compiler cannot prove self.tree will live as
        // long as the thread will run
        struct TreePtr(*const OneShotGeneralisedSuffixTree);
        unsafe impl Send for TreePtr {}

        let (send, recv): (
            std::sync::mpsc::SyncSender<()>,
            std::sync::mpsc::Receiver<()>,
        ) = std::sync::mpsc::sync_channel(self.tree.len());

        let tree: TreePtr = TreePtr(&self.tree);

        let thread = std::thread::spawn(move || {
            let tree: &OneShotGeneralisedSuffixTree = unsafe { &*tree.0 };

            let mut shared_fragments: Vec<Vec<Vec<String>>> = Vec::with_capacity(tree.len());

            (0..tree.len())
                .into_par_iter()
                .map_init(
                    || rand::thread_rng(),
                    |mut rng, i| {
                        let fragments =
                            extract_all_shared_fragments_impl(tree, threshold, debug, &mut rng, i);

                        match send.send(()) {
                            _ => (), // ignore
                        }

                        fragments
                    },
                )
                .collect_into_vec(&mut shared_fragments);

            shared_fragments
        });

        for _ in recv.into_iter() {
            if let Some(progress) = progress {
                match progress.call0() {
                    _ => (), // ignore
                }
            }
        }

        // The error from the thread cannot be handled gracefully, propagating is encouraged
        // (see https://doc.rust-lang.org/std/thread/type.Result.html)
        thread.join().unwrap()
    }

    #[args(threshold = "0.1f64", progress = "None", debug = "false")]
    pub fn extract_all_shared_fragments_for_all_strings_sequential(
        &self,
        py: Python,
        threshold: Option<f64>,
        progress: Option<&PyAny>,
        debug: bool,
    ) -> Vec<Vec<Vec<String>>> {
        let mut shared_fragments: Vec<Vec<Vec<String>>> = Vec::with_capacity(self.tree.len());

        (0..self.tree.len()).for_each(|i| {
            py.allow_threads(|| {
                shared_fragments.push(extract_all_shared_fragments_impl(
                    &self.tree,
                    threshold,
                    debug,
                    &mut rand::thread_rng(),
                    i,
                ));
            });

            if let Some(progress) = progress {
                match progress.call0() {
                    _ => (), // ignore
                }
            }
        });

        shared_fragments
    }

    #[args(debug = "false")]
    pub fn extract_longest_common_non_overlapping_substrings(
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

/// A Python module implemented in Rust.
#[pymodule]
pub fn athena(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<SharedFragmentTree>()?;

    Ok(())
}
