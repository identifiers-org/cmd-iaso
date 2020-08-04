use std::io;
use std::iter::Peekable;
use std::slice::Iter;

pub struct PackingReader<'b> {
    bytes: Peekable<Iter<'b, u8>>, // peekable iterator over the remaining bytes
    mask: Option<u8>,              // mask byte of the next chunk
    buffer: [u8; 8],               // buffer for an unpacked eight-byte chunk
    buffered: usize,               // number of bytes remaining in the buffer
}

impl<'b> PackingReader<'b> {
    pub fn new(bytes: &'b [u8]) -> Self {
        let mut bytes = bytes.iter().peekable();

        PackingReader {
            mask: bytes.next().copied(),
            bytes,
            buffer: [0; 8],
            buffered: 0,
        }
    }
}

impl<'b> io::Read for PackingReader<'b> {
    fn read(&mut self, mut buf: &mut [u8]) -> io::Result<usize> {
        let mut read = 0;

        // Fill up the provided buf
        while !buf.is_empty() {
            if self.buffered > 0 {
                // Fill up the remainder of buf with the start of the buffer
                if self.buffered > buf.len() {
                    read += buf.len();

                    buf.copy_from_slice(&self.buffer[0..buf.len()]);
                    self.buffer.rotate_left(buf.len());
                    self.buffered -= buf.len();

                    break;
                }

                // Fill the next part of buf with the remainder of the buffer
                read += self.buffered;

                buf[0..self.buffered].copy_from_slice(&self.buffer[0..self.buffered]);
                buf = &mut buf[self.buffered..];
                self.buffered = 0;
            } else if self.mask.is_none() {
                // The input bytes have been exhausted and all unpacked bytes have been returned
                break;
            }

            // Check if there is a new chunk to unpack
            if let Some(mask) = self.mask {
                if mask == 0x00u8 {
                    // Unpack eight zero bytes
                    self.buffer.iter_mut().for_each(|b| *b = 0x00u8);
                } else {
                    // Unpack a mixture of zero and non-zero bytes
                    let mut marker = 0x80u8;

                    for b in &mut self.buffer {
                        if (mask & marker) != 0x00u8 {
                            *b = *self.bytes.next().unwrap()
                        } else {
                            *b = 0x00u8
                        };

                        marker >>= 1;
                    }
                }

                self.buffered = 8;

                self.mask = self.bytes.next().copied();

                // Check if the unpacked chunk was the last one and needs to be truncated
                if let Some(next_mask) = self.mask {
                    if next_mask != 0x00u8 && self.bytes.peek().is_none() {
                        self.buffered -= next_mask.count_zeros() as usize;
                        self.mask = None;
                    }
                }
            }
        }

        Ok(read)
    }
}
