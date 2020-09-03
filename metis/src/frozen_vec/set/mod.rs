use std::borrow::Borrow;
use std::cmp::Ordering;
use std::fmt;
use std::iter::FromIterator;
use std::slice::Iter;

mod serde;

/// A frozen set which stores its elements in an ordered sequence.
pub struct FrozenVecSet<T: Ord + PartialEq>(Box<[T]>);

impl<T: Clone + Ord + PartialEq> Clone for FrozenVecSet<T> {
    fn clone(&self) -> Self {
        FrozenVecSet(self.0.clone())
    }
}

impl<T: Ord + PartialEq> FrozenVecSet<T> {
    /// Creates a new empty `FrozenVecSet<T>`.
    #[inline]
    pub fn empty() -> FrozenVecSet<T> {
        FrozenVecSet(Box::default())
    }

    /// Returns an iterator over the elements.
    #[inline]
    pub fn iter(&self) -> Iter<'_, T> {
        self.0.iter()
    }

    /// Returns the number of elements in the `FrozenVecSet<T>`.
    #[inline]
    pub fn len(&self) -> usize {
        self.0.len()
    }

    /// Returns `true` iff the `FrozenVecSet<T>` contains no elements.
    #[inline]
    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }

    /// Returns `true` iff this `FrozenVecSet<T>` is a subset of the `other` `FrozenVecSet<T>`.
    pub fn is_subset(&self, other: &FrozenVecSet<T>) -> bool {
        let mut i = 0;
        let mut j = 0;

        while i < self.0.len() && j < other.0.len() {
            match self.0[i].cmp(&other.0[j]) {
                Ordering::Greater => j += 1,
                Ordering::Equal => {
                    i += 1;
                    j += 1;
                }
                Ordering::Less => return false,
            }
        }

        i >= self.0.len()
    }

    /// Returns `Some(index)` iff `x` is stored at `index` in the `FrozenVecSet<T>`.
    /// Returns `None` iff `x` is not contained in the `FrozenVecSet<T>`.
    #[inline]
    pub fn find(&self, x: &T) -> Option<usize> {
        self.0.binary_search(x).ok()
    }
}

impl<T: Clone + Ord + PartialEq> FrozenVecSet<T> {
    /// Returns the intersection of this `FrozenVecSet<T>` and the `other` `FrozenVecSet<T>`.
    pub fn intersection(&self, other: &FrozenVecSet<T>) -> FrozenVecSet<T> {
        let mut i = 0;
        let mut j = 0;

        let mut vec = Vec::with_capacity(usize::min(self.0.len(), other.0.len()));

        while i < self.0.len() && j < other.0.len() {
            match self.0[i].cmp(&other.0[j]) {
                Ordering::Greater => j += 1,
                Ordering::Equal => {
                    vec.push(self.0[i].clone());
                    i += 1;
                    j += 1;
                }
                Ordering::Less => i += 1,
            }
        }

        FrozenVecSet(vec.into_boxed_slice())
    }
}

impl<T: Ord + PartialEq> From<Vec<T>> for FrozenVecSet<T> {
    fn from(mut vec: Vec<T>) -> Self {
        vec.sort_unstable();
        vec.dedup();
        FrozenVecSet(vec.into_boxed_slice())
    }
}

impl<T: Ord + PartialEq> FromIterator<T> for FrozenVecSet<T> {
    fn from_iter<I: IntoIterator<Item = T>>(iter: I) -> Self {
        let mut vec: Vec<T> = iter.into_iter().collect();
        vec.sort_unstable();
        vec.dedup();
        FrozenVecSet(vec.into_boxed_slice())
    }
}

impl<T: Ord + PartialEq> AsRef<[T]> for FrozenVecSet<T> {
    fn as_ref(&self) -> &[T] {
        &self.0
    }
}

impl<T: Ord + PartialEq> Borrow<[T]> for FrozenVecSet<T> {
    fn borrow(&self) -> &[T] {
        &self.0
    }
}

impl<T: fmt::Debug + Ord + PartialEq> fmt::Debug for FrozenVecSet<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_set().entries(self.iter()).finish()
    }
}
