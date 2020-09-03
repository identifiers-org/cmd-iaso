use pyo3::prelude::*;

use metis::{OneShotGeneralisedSuffixTree, WordString};

mod extract;
mod pickle;

/// A Generalised Suffix Tree which can compute the shared fragments
/// of its input text fragments.
#[pyclass(module = "athena")]
#[text_signature = "(input, /)"]
pub struct SharedFragmentTree {
    tree: OneShotGeneralisedSuffixTree,
}

#[pyproto]
impl pyo3::PyObjectProtocol for SharedFragmentTree {
    /// Prints a debug view of the entire suffix tree.
    fn __str__(&self) -> PyResult<String> {
        Ok(format!("{:?}", self.tree))
    }
}

#[pyproto]
impl pyo3::PySequenceProtocol for SharedFragmentTree {
    /// Returns the number of word strings stored in the tree.
    fn __len__(&self) -> usize {
        self.tree.len()
    }
}

#[pymethods]
impl SharedFragmentTree {
    /// Creates a new `SharedFragmentTree` with the ordered sequence of
    /// word strings in `input`.
    #[new]
    #[args(input = "vec![]")]
    pub fn new(input: Vec<Vec<String>>) -> Self {
        SharedFragmentTree {
            tree: OneShotGeneralisedSuffixTree::new(
                input.into_iter().map(WordString::from).collect(),
            ),
        }
    }

    /// Returns the total number of words stored internally in the tree.
    #[getter]
    pub fn size(&self) -> usize {
        self.tree.size()
    }
}
