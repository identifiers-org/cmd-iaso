use bit_set::BitSet;
use std::iter::FromIterator;

use metis::{
    all_any_set::AllAnySet, one_shot_generalised_suffix_tree::OneShotGeneralisedSuffixTree,
    word_string::WordString,
};

#[test]
fn system_test() {
    let strings = vec![
        WordString::from(vec!["a", "b", "c", "d", "e"]),
        WordString::from(vec!["a", "b", "c"]),
        WordString::from(vec!["c", "d", "e"]),
        WordString::from(vec!["b", "c"]),
    ];

    let tree = OneShotGeneralisedSuffixTree::new(strings);

    let string_indices = match AllAnySet::new(BitSet::from_iter(0..1), BitSet::from_iter(1..4)) {
        Some(string_indices) => string_indices,
        None => panic!("All set is empty"),
    };

    let lcnos = tree.extract_longest_common_non_overlapping_substrings(string_indices, None, false);

    assert_eq!(
        lcnos,
        vec![
            (WordString::from(vec!["c", "d", "e"]), 2),
            (WordString::from(vec!["a", "b"]), 0)
        ]
    );
}
