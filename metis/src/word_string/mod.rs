use std::iter::FromIterator;
use std::ops::Index;

mod serde;

/// A contiguous immutable array type which stores a string of words `[String]`.
#[derive(Hash, Eq, PartialEq, Debug, Default)]
pub struct WordString(Vec<String>);

impl WordString {
    /// Returns the number of words in the `WordString`, also referred to as its 'length'.
    #[inline]
    pub fn len(&self) -> usize {
        self.0.len()
    }

    /// Returns `true` iff the `WordString` contains no words.
    #[inline]
    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }
}

impl From<Vec<String>> for WordString {
    #[inline]
    fn from(vec: Vec<String>) -> Self {
        WordString(vec)
    }
}

impl From<Vec<&str>> for WordString {
    #[inline]
    fn from(vec: Vec<&str>) -> Self {
        WordString(vec.into_iter().map(String::from).collect())
    }
}

impl From<&[String]> for WordString {
    #[inline]
    fn from(slice: &[String]) -> Self {
        WordString(slice.to_vec())
    }
}

impl Into<Vec<String>> for WordString {
    #[inline]
    fn into(self) -> Vec<String> {
        self.0
    }
}

impl IntoIterator for WordString {
    type Item = String;
    type IntoIter = std::vec::IntoIter<Self::Item>;

    #[inline]
    fn into_iter(self) -> Self::IntoIter {
        self.0.into_iter()
    }
}

impl FromIterator<String> for WordString {
    #[inline]
    fn from_iter<I: IntoIterator<Item = String>>(iter: I) -> Self {
        WordString(iter.into_iter().collect())
    }
}

impl<R> Index<R> for WordString
where
    Vec<String>: Index<R>,
{
    type Output = <Vec<String> as Index<R>>::Output;

    #[inline]
    fn index(&self, index: R) -> &Self::Output {
        &self.0[index]
    }
}
