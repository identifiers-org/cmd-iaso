//! `metis` implements a Generalised Suffix Tree for strings of words
//! which can extract all common non-overlapping substrings in one go.
//!
//! # Examples
//!
//! ```
//! use std::iter::FromIterator;
//! use metis::*;
//!
//! let strings = vec![
//!     WordString::from(vec!["a", "b", "c", "d", "e"]),
//!     WordString::from(vec!["a", "b", "c"]),
//!     WordString::from(vec!["c", "d", "e"]),
//!     WordString::from(vec!["b", "c"]),
//! ];
//!
//! let tree = OneShotGeneralisedSuffixTree::new(strings);
//!
//! let string_indices = AllAnySet::new(
//!     FrozenVecSet::from_iter(0..1),
//!     FrozenVecSet::from_iter(1..4),
//! ).unwrap(); // cannot fail here as the `all` set is non-empty
//!
//! let lcnos = tree.extract_longest_common_non_overlapping_substrings(
//!     string_indices, None, false
//! );
//!
//! assert_eq!(
//!     lcnos,
//!     vec![
//!         (WordString::from(vec!["c", "d", "e"]), 2),
//!         (WordString::from(vec!["a", "b"]), 0)
//!     ]
//! );
//! ```

#![deny(clippy::all)]
#![deny(missing_docs)]

mod all_any_set;
mod frozen_vec;
mod one_shot_generalised_suffix_tree;
mod word_string;

pub use all_any_set::AllAnySet;
pub use frozen_vec::set::FrozenVecSet;
pub use one_shot_generalised_suffix_tree::{EarlyStopCallback, OneShotGeneralisedSuffixTree};
pub use word_string::WordString;
