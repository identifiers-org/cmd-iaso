use bit_set::BitSet;
use bit_vec::BitVec;

use std::iter::FromIterator;

mod find;

use find::find_longest_common_substring_per_index;

use super::{AllAnySet, Node, NodeRef, WordString, EarlyStopCallback};

#[allow(clippy::too_many_arguments)]
pub fn extract_longest_common_non_overlapping_substrings(
    primary_length: usize,
    offset: usize,
    root_ref: NodeRef,
    nodes: &[Node],
    word: &[String],
    string_indices: AllAnySet,
    early_stop: EarlyStopCallback,
    debug: bool,
) -> Vec<(WordString, usize)> {
    assert_ne!(primary_length, 0);

    let mut index_lengths = vec![0; primary_length];

    find_longest_common_substring_per_index(nodes, root_ref, string_indices, &mut index_lengths);

    let mut substrings: Vec<(usize, usize)> = index_lengths
        .into_iter()
        .enumerate()
        .map(|(i, l)| (l, i))
        .collect();
    substrings.sort_unstable();

    let mut remaining_string: BitSet =
        BitSet::from_bit_vec(BitVec::from_elem(primary_length, true));

    let mut longest_common_non_overlapping_substrings: Vec<(WordString, usize)> = Vec::new();

    let mut longest_non_overlapping_substring_length = substrings[substrings.len() - 1].0;

    if debug {
        println!(
            "{:?} {:?}",
            longest_non_overlapping_substring_length, substrings
        );
    }

    while !substrings.is_empty() && longest_non_overlapping_substring_length >= 1 {
        let mut i = substrings.len() - 1;

        while i < substrings.len() && substrings[i].0 >= longest_non_overlapping_substring_length {
            let start = substrings[i].1;

            if !remaining_string.contains(start) {
                substrings.remove(i);
                i = i.wrapping_sub(1);
                continue;
            }

            if !remaining_string.contains(start + longest_non_overlapping_substring_length - 1) {
                i = i.wrapping_sub(1);
                continue;
            }

            let substring: BitSet<u32> =
                BitSet::from_iter(start..(start + longest_non_overlapping_substring_length));

            if !remaining_string.is_superset(&substring) {
                i = i.wrapping_sub(1);
                continue;
            }

            remaining_string.difference_with(&substring);

            longest_common_non_overlapping_substrings.push((
                WordString::from(
                    &word[(offset + start)
                        ..(offset + start + longest_non_overlapping_substring_length)],
                ),
                start,
            ));

            if early_stop(
                primary_length,
                &mut longest_common_non_overlapping_substrings,
            ) {
                return longest_common_non_overlapping_substrings;
            }

            substrings.remove(i);
            break;
        }

        if i > substrings.len()
            || (i < substrings.len() && substrings[i].0 < longest_non_overlapping_substring_length)
        {
            longest_non_overlapping_substring_length -= 1;
        }

        if debug {
            println!(
                "{:?} {:?}",
                longest_non_overlapping_substring_length, substrings
            );
        }
    }

    longest_common_non_overlapping_substrings
}
