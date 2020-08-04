use rand::{self, Rng};
use std::io::{Read, Write};

use super::*;

#[test]
fn test_that_packing_unpacking_is_bijective() {
    let mut rng = rand::thread_rng();
    let mut input: Vec<u8> = Vec::with_capacity(100);

    for len in 1..=100 {
        input.resize(len, 0);
        rng.fill(&mut input[..]);

        input.iter_mut().for_each(|i| {
            if rng.gen_bool(3.0f64 / 8.0f64) {
                *i = 0u8;
            }
        });

        let packed_size =
            size::PackingSize::calc_size(len, bytecount::count(&input, 0x00u8)).unwrap();

        let mut packed = vec![0; packed_size];

        writer::PackingWriter::new(&mut packed)
            .write_all(&input)
            .unwrap();

        let mut output = Vec::with_capacity(input.len());

        reader::PackingReader::new(&packed)
            .read_to_end(&mut output)
            .unwrap();

        assert_eq!(input, output);
    }
}
