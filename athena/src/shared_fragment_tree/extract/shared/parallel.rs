use pyo3::prelude::*;

use rayon::prelude::*;

use metis::one_shot_generalised_suffix_tree::OneShotGeneralisedSuffixTree;

use super::{extract_all_shared_fragments_impl, SharedFragmentTree};

#[pymethods]
impl SharedFragmentTree {
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
