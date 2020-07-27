use bit_set::BitSet;
use std::iter::FromIterator;
use tinyset::SetUsize as TinySet;
use vec_map::VecMap;

pub struct AllAnySet {
    all: BitSet,
    any: BitSet,

    primary_index: usize,
}

impl AllAnySet {
    pub fn new(all: BitSet, any: BitSet) -> Option<AllAnySet> {
        Some(AllAnySet {
            primary_index: match all.iter().next() {
                Some(primary_index) => primary_index,
                None => return None,
            },

            all,
            any,
        })
    }

    pub fn subset(&self, other: &VecMap<TinySet>) -> Option<AllAnySet> {
        if !self.all.iter().all(|index| other.contains_key(index)) {
            return None;
        };

        if self.any.is_empty() {
            return Some(AllAnySet {
                all: self.all.clone(),
                any: BitSet::new(),
                primary_index: self.primary_index,
            });
        };

        let new_any = BitSet::from_iter(self.any.iter().filter(|index| other.contains_key(*index)));

        if new_any.is_empty() {
            return None;
        };

        return Some(AllAnySet {
            all: self.all.clone(),
            any: new_any,

            primary_index: self.primary_index,
        });
    }

    #[inline]
    pub fn primary_index(&self) -> usize {
        self.primary_index
    }
}
