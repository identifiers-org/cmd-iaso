use std::io;

pub struct PackingSize {
    total: usize,
    zeroes: usize,
}

pub struct PackingSizeWriter<'s>(&'s mut PackingSize);

impl PackingSize {
    pub fn new() -> Self {
        PackingSize {
            total: 0,
            zeroes: 0,
        }
    }

    pub fn writer(&mut self) -> PackingSizeWriter {
        PackingSizeWriter(self)
    }

    pub fn size(self) -> usize {
        Self::calc_size(self.total, self.zeroes).unwrap()
    }

    pub fn calc_size(total: usize, zeroes: usize) -> Option<usize> {
        // The packed output will contain
        // - all non-zero bytes
        // - one header byte for every started eight byte chunk
        // - one footer byte if the total number of bytes is not a multiple of 8

        if total >= zeroes {
            Some((total - zeroes) + total / 8 + if total % 8 == 0 { 0 } else { 2 })
        } else {
            None
        }
    }
}

impl<'s> io::Write for PackingSizeWriter<'s> {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize> {
        self.0.total += buf.len();
        self.0.zeroes += bytecount::count(buf, 0x00u8);

        Ok(buf.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
