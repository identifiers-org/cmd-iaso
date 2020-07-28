use bit_set::BitSet;
use std::iter::FromIterator;
use tinyset::SetUsize as TinySet;
use vec_map::VecMap;

/// A special set of `usize` which contains both an `all` and and `any` part.
pub struct AllAnySet {
    all: BitSet,
    any: BitSet,

    primary_index: usize,
}

impl AllAnySet {
    /// Creates a new AllAnySet with the `all` and `any` part.
    /// Iff `all.is_empty()` the constructor will return `None`.
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

    /// Returns true if the set is a subset of the set of keys of `other`.
    /// A subset must contain all the elements in this `AllAnySet`'s `all` set.
    /// A subset must contain at least on of the elements in this `AllAnySet`'s
    /// `any` set iff the `any` set is non-empty.
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

        Some(AllAnySet {
            all: self.all.clone(),
            any: new_any,

            primary_index: self.primary_index,
        })
    }

    /// Returns an element in the `all` set. The element returned is always the same.
    #[inline]
    pub fn primary_index(&self) -> usize {
        self.primary_index
    }
}
