use std::fmt;

mod build;
mod lcnos;
mod node;
mod serde;

use super::all_any_set::AllAnySet;
use super::frozen_vec::flattened_map::FrozenFlattenedVecMap;
use super::word_string::WordString;
use build::build;
use lcnos::extract_longest_common_non_overlapping_substrings;
use node::{Node, NodeRef};

/// An alias for the type signature of the `early_stop` callback for the
/// `extract_longest_common_non_overlapping_substrings` method of the
/// `OneShotGeneralisedSuffixTree`.
pub type EarlyStopCallback<'a> = &'a mut dyn FnMut(usize, &mut Vec<(WordString, usize)>) -> bool;

/// A Generalised Suffix Tree which computes all longest common non-overlapping
/// substrings in one go.
pub struct OneShotGeneralisedSuffixTree {
    nodes: Vec<Node>,
    root_ref: NodeRef,

    word: WordString,
    word_starts: Vec<usize>,
}

impl fmt::Debug for OneShotGeneralisedSuffixTree {
    fn fmt(&self, fmt: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt.write_fmt(format_args!(
            "OneShotGeneralisedSuffixTree {{ word: {:?} word_starts: {:?} root:\n  ",
            self.word, self.word_starts
        ))?;

        self.nodes[self.root_ref].fmt_rec(self, 2, fmt)?;

        fmt.write_str("\n}")
    }
}

impl OneShotGeneralisedSuffixTree {
    /// Creates a new `OneShotGeneralisedSuffixTree` with the ordered sequence of
    /// `WordString`s in `input`.
    pub fn new(input: Vec<WordString>) -> OneShotGeneralisedSuffixTree {
        let (nodes, root_ref, word, word_starts) = build(input);

        OneShotGeneralisedSuffixTree {
            nodes,
            root_ref,

            word,
            word_starts,
        }
    }

    /// Returns the number of `WordString`s stored in the tree.
    pub fn len(&self) -> usize {
        self.word_starts.len()
    }

    /// Returns `true` iff the tree contains no `WordString`s.
    pub fn is_empty(&self) -> bool {
        self.word_starts.is_empty()
    }

    /// Returns the total number of words stored internally in the tree.
    pub fn size(&self) -> usize {
        self.word.len()
    }

    fn no_early_stop(_: usize, _: &mut Vec<(WordString, usize)>) -> bool {
        false
    }

    /// Extracts all common non-overlapping substrings of the input `WordString`s
    /// in one go. The output will be ordered decreasingly by substring length.
    /// For each substring, it will also report its start index in
    /// `input[string_indices.primary_index()]`.
    ///
    /// `string_indices` specifies the `AllAnySet` which selects which of the input
    /// `WordString`s to consider for common substring extraction.
    ///
    /// `early_stop` is an optional callback which can be used to terminate the algorithm
    /// early on iff it returns `true`. It is called after each extracted fragment.
    ///
    /// Iff `debug` is `true`, the state of extraction will be printed after each iteration.
    pub fn extract_longest_common_non_overlapping_substrings(
        &self,
        string_indices: AllAnySet,
        early_stop: Option<EarlyStopCallback>,
        debug: bool,
    ) -> Vec<(WordString, usize)> {
        // We require the primary index to be a valid input string index
        // If it is not, the AllAnySet will never be a subset
        // Therefore, there will be no common substrings
        if string_indices.primary_index() >= self.word_starts.len() {
            return vec![];
        };

        let primary_length = (if (string_indices.primary_index() + 1) >= self.word_starts.len() {
            self.word.len()
        } else {
            self.word_starts[string_indices.primary_index() + 1]
        }) - self.word_starts[string_indices.primary_index()]
            - 1;

        if primary_length == 0 {
            return vec![];
        };

        let offset = self.word_starts[string_indices.primary_index()];

        let no_early_stop = &mut OneShotGeneralisedSuffixTree::no_early_stop;

        let early_stop: EarlyStopCallback = match early_stop {
            Some(early_stop) => early_stop,
            None => no_early_stop,
        };

        extract_longest_common_non_overlapping_substrings(
            primary_length,
            offset,
            self.root_ref,
            &self.nodes,
            &self.word[..],
            string_indices,
            early_stop,
            debug,
        )
    }
}
