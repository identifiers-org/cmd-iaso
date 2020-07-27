use pyo3::import_exception;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use bincode;

mod packing;

import_exception!(pickle, PicklingError);
import_exception!(pickle, UnpicklingError);

use super::SharedFragmentTree;

#[pymethods]
impl SharedFragmentTree {
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
}
