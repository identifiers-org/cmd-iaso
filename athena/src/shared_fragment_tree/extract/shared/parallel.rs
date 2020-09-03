use pyo3::prelude::*;

use rayon::prelude::*;

use metis::OneShotGeneralisedSuffixTree;

use super::{extract_all_shared_fragments_impl, SharedFragmentTree};

#[pymethods]
impl SharedFragmentTree {
    /// For each string in the tree, it extracts all text fragments shared
    /// with at least one other fragment in the tree.
    ///
    /// This method is parallelised internally by using the `rayon` crate.
    /// It can, therefore, not be parallelised externally.
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
                .map_init(rand::thread_rng, |mut rng, i| {
                    let fragments =
                        extract_all_shared_fragments_impl(tree, threshold, debug, &mut rng, i);

                    let _ = send.send(()); // ignore result

                    fragments
                })
                .collect_into_vec(&mut shared_fragments);

            shared_fragments
        });

        for _ in recv.into_iter() {
            if let Some(progress) = progress {
                let _ = progress.call0(); // ignore result
            }
        }

        // The error from the thread cannot be handled gracefully, propagating is encouraged
        // (see https://doc.rust-lang.org/std/thread/type.Result.html)
        thread.join().unwrap()
    }
}
