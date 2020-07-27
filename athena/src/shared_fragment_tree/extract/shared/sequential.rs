use pyo3::prelude::*;

use super::{extract_all_shared_fragments_impl, SharedFragmentTree};

#[pymethods]
impl SharedFragmentTree {
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
}
