use pyo3::prelude::*;

    mod shared_fragment_tree;
use shared_fragment_tree::SharedFragmentTree;

/// A Python module implemented in Rust.
#[pymodule]
pub fn athena(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<SharedFragmentTree>()?;

    Ok(())
}
