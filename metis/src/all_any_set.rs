use super::FrozenVecSet;

/// A special set of `usize` which contains both an `all` and and `any` part.
pub struct AllAnySet {
    all: FrozenVecSet<usize>,
    any: FrozenVecSet<usize>,

    primary_index: usize,
}

impl AllAnySet {
    /// Creates a new AllAnySet with the `all` and `any` part.
    /// Iff `all.is_empty()` the constructor will return `None`.
    pub fn new(all: FrozenVecSet<usize>, any: FrozenVecSet<usize>) -> Option<AllAnySet> {
        Some(AllAnySet {
            primary_index: match all.as_ref().first() {
                Some(primary_index) => *primary_index,
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
    pub fn subset(&self, other: &FrozenVecSet<usize>) -> Option<AllAnySet> {
        if !self.all.is_subset(other) {
            return None;
        }

        if self.any.is_empty() {
            return Some(AllAnySet {
                all: self.all.clone(),
                any: FrozenVecSet::empty(),
                primary_index: self.primary_index,
            });
        };

        let new_any = self.any.intersection(other);

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
