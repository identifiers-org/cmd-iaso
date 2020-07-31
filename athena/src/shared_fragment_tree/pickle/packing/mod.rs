#[cfg(test)]
mod tests;

pub fn pack(mut bytes: Vec<u8>) -> Vec<u8> {
    let initial_len = bytes.len();
    let upper_bound = (((initial_len as f64) * 1.125f64).ceil() as usize) + 1;

    // More efficient packing by reusing the buffer we are packing as the output
    bytes.resize(upper_bound, 0u8);

    // TODO: Explain

    let mut write_it = upper_bound;
    let mut read_it = initial_len;

    let mut buffer: [u8; 8] = [0; 8];

    match initial_len % 8 {
        0 => (),
        rem => {
            write_it -= 1;

            bytes[write_it] = 0xFFu8.wrapping_shl(8u32 - (rem as u32));

            let mut mask = 0x00u8;
            let mut marker = 0x80u8;

            let mut compressed = 0;

            for byte in bytes[(initial_len - rem)..initial_len].iter() {
                if *byte != 0x00u8 {
                    mask |= marker;
                    buffer[compressed] = *byte;
                    compressed += 1;
                }

                marker >>= 1;
            }

            if compressed > 0 {
                bytes[(write_it - compressed)..write_it].copy_from_slice(&buffer[0..compressed]);
                write_it -= compressed;
            }

            write_it -= 1;

            bytes[write_it] = mask;

            read_it -= rem;
        }
    }

    for _ in 0..(read_it / 8) {
        let mut mask = 0x00u8;
        let mut marker = 0x80u8;

        let mut compressed = 0;

        for byte in bytes[(read_it - 8)..read_it].iter() {
            if *byte != 0x00u8 {
                mask |= marker;
                buffer[compressed] = *byte;
                compressed += 1;
            }

            marker >>= 1;
        }

        if compressed > 0 {
            bytes[(write_it - compressed)..write_it].copy_from_slice(&buffer[0..compressed]);
            write_it -= compressed;
        }

        write_it -= 1;

        bytes[write_it] = mask;

        read_it -= 8;
    }

    bytes.rotate_left(write_it);
    bytes.truncate(upper_bound - write_it);

    bytes
}

pub fn unpack(bytes: &[u8]) -> Vec<u8> {
    // Underallocate so the output only grows as necessary
    let mut unpacked = Vec::with_capacity(bytes.len());

    let mut bytes_iter = bytes.iter().peekable();

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
