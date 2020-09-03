use std::io;

pub struct PackingWriter<'b> {
    bytes: &'b mut [u8], // output buffer to which the packed bytes will be written
    buffer: [u8; 8],     // buffer for an unpacked eight-byte chunk
    buffered: usize,     // number of bytes already in the buffer
    written: usize,      // number of bytes already written to the output
}

impl<'b> PackingWriter<'b> {
    pub fn new(bytes: &'b mut [u8]) -> Self {
        PackingWriter {
            bytes,
            buffer: [0; 8],
            buffered: 0,
            written: 0,
        }
    }
}

impl<'b> Drop for PackingWriter<'b> {
    // drop will be called when the PackingWriter goes out of scope
    fn drop(&mut self) {
        // The output only needs to be amended if not all bytes have been packed
        //  and flushed yet
        if self.buffered == 0 {
            return;
        }

        let mut mask = 0x00u8;
        let mut marker = 0x80u8;
        let mut written = 0;

        // Pack and write the remaining bytes from the buffer to the output
        for byte in self.buffer[0..self.buffered].iter() {
            if *byte != 0x00u8 {
                mask |= marker;
                written += 1;
                self.bytes[self.written + written] = *byte;
            }

            marker >>= 1;
        }

        // Write the final chunk header and closing footer to the output
        self.bytes[self.written] = mask;
        self.bytes[self.written + written + 1] = 0xFFu8.wrapping_shl(8u32 - (self.buffered as u32));
    }
}

impl<'b> io::Write for PackingWriter<'b> {
    fn write(&mut self, mut buf: &[u8]) -> io::Result<usize> {
        let received = buf.len();

        // Drain out the provided buf
        while !buf.is_empty() {
            // Fill up more of the buffer with the remainder of buf
            if buf.len() < (8 - self.buffered) {
                self.buffer[self.buffered..(self.buffered + buf.len())].copy_from_slice(buf);
                self.buffered += buf.len();

                break;
            }

            // Full up the buffer with the next part of buf
            self.buffer[self.buffered..8].copy_from_slice(&buf[0..(8 - self.buffered)]);
            buf = &buf[(8 - self.buffered)..];
            self.buffered = 0;

            let mut mask = 0x00u8;
            let mut marker = 0x80u8;
            let mut written = 0;

            // Pack and write the next chunk to the output
            for byte in self.buffer.iter() {
                if *byte != 0x00u8 {
                    mask |= marker;
                    written += 1;
                    self.bytes[self.written + written] = *byte;
                }

                marker >>= 1;
            }

            // Write the chunk's header to the output
            self.bytes[self.written] = mask;

            // Advance the write head of the output
            self.written += 1 + written;
        }

        Ok(received)
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
