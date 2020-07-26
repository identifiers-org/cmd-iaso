pub fn pack(bytes: &[u8]) -> Vec<u8> {
    let mut packed = Vec::with_capacity((((bytes.len() as f64) * 1.125f64).ceil() as usize) + 1);

    let mut buffer = Vec::with_capacity(8);

    for slice in bytes.chunks(8) {
        let mut mask = 0x00u8;
        let mut marker = 0x80u8;

        for byte in slice {
            if *byte != 0x00u8 {
                mask |= marker;
                buffer.push(*byte);
            }

            marker >>= 1;
        }

        packed.push(mask);
        packed.append(&mut buffer);
    }

    match bytes.len() % 8 {
        0 => (),
        l => packed.push(0xFFu8.wrapping_shl(8u32 - (l as u32))),
    };

    packed.shrink_to_fit();

    packed
}

pub fn unpack(bytes: &[u8]) -> Vec<u8> {
    let mut unpacked = Vec::with_capacity(bytes.len() * 8);

    let mut bytes_iter = bytes.into_iter().peekable();

    while let Some(byte) = bytes_iter.next() {
        let mask = *byte;

        if mask != 0x00u8 && bytes_iter.peek().is_none() {
            unpacked.truncate(unpacked.len() - (mask.count_zeros() as usize));

            break;
        };

        if mask == 0x00u8 {
            unpacked.resize(unpacked.len() + 8, 0x00u8);

            continue;
        };

        let mut marker = 0x80u8;

        for _ in 0..8 {
            if (mask & marker) != 0x00u8 {
                unpacked.push(*bytes_iter.next().unwrap())
            } else {
                unpacked.push(0x00u8)
            };

            marker >>= 1;
        }
    }

    unpacked.shrink_to_fit();

    unpacked
}
