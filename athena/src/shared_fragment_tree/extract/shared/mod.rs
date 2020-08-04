use metis::{AllAnySet, FrozenVecSet, OneShotGeneralisedSuffixTree, WordString};

use rand::{
    self,
    distributions::{DistIter, Distribution, Uniform},
    rngs::ThreadRng,
    Rng,
};
use std::iter::FromIterator;

use super::SharedFragmentTree;

mod parallel;
mod sequential;

fn shared_early_stop<D: Distribution<f64>, R: Rng>(
    rng_iter: &mut DistIter<D, R, f64>,
    threshold: f64,
    #[allow(non_snake_case)] L: usize,
    fragments: &mut Vec<(WordString, usize)>,
) -> bool {
    // Upper-bound threshold of unique information where a response is considered to
    // contain not enough unique information
    let threshold = threshold;

    // Number of words in the input document
    #[allow(non_snake_case)]
    let L = L as f64;
    // Number of words which have already been matched in shared fragments
    #[allow(non_snake_case)]
    let C = fragments
        .iter()
        .map(|(fragment, _)| fragment.len())
        .sum::<usize>() as f64;
    // Number of fragments found so far
    let n = fragments.len() as f64;
    // Number of words in the latest fragment, i.e. the maximum fragment size possible
    // for the rest of the document
    let f_n = fragments[fragments.len() - 1].0.len() as f64;
    // Measure of unique information (not shared) in the document, in range 0% - 100%
    let min_unique_information = (n + f64::ceil((L - C) / f_n) - 1.0f64) / L;
    let max_unique_information = (L - C + n - 1.0f64) / L;

    // Russian Roulette probability of stopping early
    let p = f64::sqrt(f64::max(
        f64::max(
            (min_unique_information - threshold) / (1.0f64 - threshold),
            (threshold - max_unique_information) / threshold,
        ),
        0.0f64,
    ));

    // Stop early iff (the minimum possible unique information is greater than the
    // threshold or the maximum possible unique information is less than the threshold)
    // and Russian Roulette has fired
    rng_iter.next().unwrap_or(0.0f64) < p
}

fn extract_all_shared_fragments_impl<'a>(
    tree: &OneShotGeneralisedSuffixTree,
    threshold: Option<f64>,
    debug: bool,
    rng: &'a mut ThreadRng,
    i: usize,
) -> Vec<Vec<String>> {
    let string_indices: AllAnySet = AllAnySet::new(
        FrozenVecSet::from_iter(i..=i),
        FrozenVecSet::from_iter((0..i).chain((i + 1)..tree.len())),
    )
    .unwrap(); // cannot fail as all set will always be {i}

    let fragments = if let Some(threshold) = threshold {
        let dist = Uniform::from(0.0f64..1.0f64);
        let mut rng_iter = dist.sample_iter(rng);

        tree.extract_longest_common_non_overlapping_substrings(
            string_indices,
            Some(&mut |#[allow(non_snake_case)] L: usize,
                       fragments: &mut Vec<(WordString, usize)>| {
                shared_early_stop(&mut rng_iter, threshold, L, fragments)
            }),
            debug,
        )
    } else {
        tree.extract_longest_common_non_overlapping_substrings(string_indices, None, debug)
    };

    fragments
        .into_iter()
        .map(|(fragments, _start)| fragments.into())
        .collect()
}
