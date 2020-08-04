use rand::{self, Rng};

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

        assert_eq!(input, unpack(&pack(input.clone())));
    }
}
