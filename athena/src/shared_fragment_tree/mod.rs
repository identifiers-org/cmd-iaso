use pyo3::prelude::*;

use metis::{
    one_shot_generalised_suffix_tree::OneShotGeneralisedSuffixTree, word_string::WordString,
};

mod extract;
mod pickle;

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
                input.into_iter().map(WordString::from).collect(),
            ),
        }
    }

    #[getter]
    pub fn size(&self) -> usize {
        self.tree.size()
    }
}
