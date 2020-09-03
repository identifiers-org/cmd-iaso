use pyo3::prelude::*;

use super::{extract_all_shared_fragments_impl, SharedFragmentTree};

#[pymethods]
impl SharedFragmentTree {
    /// For each string in the tree, it extracts all text fragments shared
    /// with at least one other fragment in the tree.
    ///
    /// This method can be executed on multiple threads in parallel as it
    /// releases the Python GIL `py`.
    ///
    /// `threshold` optionally specifies the percentage threshold between
    /// a string containing too few or enough unique (non-shared) words.
    /// Iff it set the extraction might stop early if it can prove that
    /// it has already been decised which side of the threshold the string
    /// will land on. Iff omitted, early stopping will be disabled.
    ///
    /// `progress` optionally specifies a reference to a Python callable
    /// which expects  no arguments. It will be called after all shared
    /// fragments for a string have been extracted.
    ///
    /// Iff `debug` is `true`, the state of extraction will be printed after
    /// each iteration.
    #[text_signature = "($self, /, threshold=0.1, progress=None, debug=False)"]
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
                let _ = progress.call0(); // ignore the result
            }
        });

        shared_fragments
    }
}
