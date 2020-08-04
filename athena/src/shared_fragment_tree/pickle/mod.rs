use pyo3::import_exception;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

mod packing;

import_exception!(pickle, PicklingError);
import_exception!(pickle, UnpicklingError);

use super::SharedFragmentTree;
use packing::reader::PackingReader;

#[pymethods]
impl SharedFragmentTree {
    /// Builtin function for deserialising the suffix tree from Python bytes
    /// which is used in `pickle.load()`
    #[text_signature = "($self, state, /)"]
    pub fn __setstate__(&mut self, _py: Python, state: &PyBytes) -> PyResult<()> {
        self.tree = match bincode::deserialize_from(PackingReader::new(state.as_bytes())) {
            Ok(tree) => tree,
            Err(e) => return Err(PyErr::new::<UnpicklingError, _>(format!("{}", e))),
        };

        Ok(())
    }

    /// Builtin function for serialising the suffix tree into Python bytes
    /// which is used in `pickle.dump()`
    #[text_signature = "($self)"]
    pub fn __getstate__(&self, py: Python) -> PyResult<PyObject> {
        match bincode::serialize(&self.tree) {
            Ok(bytes) => Ok(PyBytes::new(py, &packing::pack(bytes)).to_object(py)),
            Err(e) => Err(PyErr::new::<PicklingError, _>(format!("{}", e))),
        }
    }
}
