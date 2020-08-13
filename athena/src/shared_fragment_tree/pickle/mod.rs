use pyo3::import_exception;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

mod packing;

import_exception!(pickle, PicklingError);
import_exception!(pickle, UnpicklingError);

use super::SharedFragmentTree;
use packing::{reader::PackingReader, size::PackingSize, writer::PackingWriter};

#[pymethods]
impl SharedFragmentTree {
    /// Builtin function for deserialising the suffix tree from Python bytes
    /// which is used in `pickle.load()`
    #[text_signature = "($self, state, /)"]
    pub fn __setstate__(&mut self, _py: Python, state: &PyBytes) -> PyResult<()> {
        // Deserialise the tree from a reference to a Python allocated bytestring (zero-copy)
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
        let mut packing_size = PackingSize::new();

        // Predict the size of the packed serialised output
        if let Err(e) = bincode::serialize_into(packing_size.writer(), &self.tree) {
            return Err(PyErr::new::<PicklingError, _>(format!("{}", e)));
        }

        let packing_size = packing_size.size();

        // Serialise the tree to a Python allocated bytestring (zero-copy)
        Ok(PyBytes::new_with(py, packing_size, |buffer: &mut [u8]| {
            bincode::serialize_into(PackingWriter::new(buffer), &self.tree)
                .map_err(|e| PyErr::new::<PicklingError, _>(format!("{}", e)))
        })?
        .to_object(py))
    }
}
