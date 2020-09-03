use std::fmt;
use std::iter::FromIterator;
use std::ops::{Index, Range};

mod serde;

use super::set::FrozenVecSet;

/// A frozen map which associates a collection of values with every key.
pub struct FrozenFlattenedVecMap<K: Ord + PartialEq, V> {
    keys: FrozenVecSet<K>,
    value_ranges: Box<[Range<usize>]>,
    flattened_values: Box<[V]>,
}

impl<K: Ord + PartialEq, V> FrozenFlattenedVecMap<K, V> {
    /// Creates a new empty `FrozenFlattenedVecMap<K, V>`.
    pub fn empty() -> Self {
        FrozenFlattenedVecMap {
            keys: FrozenVecSet::empty(),
            value_ranges: Box::default(),
            flattened_values: Box::default(),
        }
    }

    /// Returns the keys of the `FrozenFlattenedVecMap<K, V>`.
    #[inline]
    pub fn keys(&self) -> &FrozenVecSet<K> {
        &self.keys
    }
}

impl<K: Ord + PartialEq, V> Index<&K> for FrozenFlattenedVecMap<K, V> {
    type Output = [V];

    fn index(&self, key: &K) -> &Self::Output {
        &self.flattened_values[self.value_ranges[self.keys.find(key).unwrap()].clone()]
    }
}

impl<K: Ord + PartialEq, V, VI: IntoIterator<Item = V>> FromIterator<(K, VI)>
    for FrozenFlattenedVecMap<K, V>
{
    fn from_iter<I: IntoIterator<Item = (K, VI)>>(iter: I) -> Self {
        let mut keys: Vec<K> = Vec::new();
        let mut values: Vec<Vec<V>> = Vec::new();

        for (key, vals) in iter.into_iter() {
            keys.push(key);
            values.push(vals.into_iter().collect());
        }

        if keys.is_empty() {
            return Self::empty();
        }

        let mut indices: Vec<usize> = (0..keys.len()).collect();
        indices.sort_unstable_by_key(|i| &keys[*i]);

        reorder_vec(&mut keys, indices.iter().copied());
        reorder_vec(&mut values, indices.iter().copied());

        let mut deduped_keys: Vec<K> = Vec::with_capacity(keys.len());
        let mut value_ranges: Vec<Range<usize>> = Vec::with_capacity(keys.len());
        let mut flattened_values: Vec<V> =
            Vec::with_capacity(values.iter().map(|vs| vs.len()).sum());

        for (key, vals) in keys.into_iter().zip(values.into_iter()) {
            if let Some(prev_key) = deduped_keys.last() {
                if prev_key == &key {
                    deduped_keys.pop();

                    if let Some(range) = value_ranges.pop() {
                        flattened_values.truncate(range.start);
                    }
                }
            }

            deduped_keys.push(key);
            value_ranges.push(flattened_values.len()..(flattened_values.len() + vals.len()));
            flattened_values.extend(vals);
        }

        FrozenFlattenedVecMap {
            keys: FrozenVecSet::from(deduped_keys),
            value_ranges: value_ranges.into_boxed_slice(),
            flattened_values: flattened_values.into_boxed_slice(),
        }
    }
}

/*
Based on the Rust vector-map crate by Pierre Avital
https://github.com/p-avital/vec-map-rs/blob/b85618acaeaa75144cbb5f8c6af70997ddc919c0/src/lib.rs#L223-L232
*/
fn reorder_vec<T>(vec: &mut Vec<T>, order: impl Iterator<Item = usize>) {
    use std::mem::MaybeUninit;

    let mut buffer: Vec<MaybeUninit<T>> = vec.iter().map(|_| MaybeUninit::uninit()).collect();

    for (from, to) in order.enumerate() {
        std::mem::swap(&mut vec[to], unsafe { &mut *(buffer[from].as_mut_ptr()) });
    }

    for i in 0..vec.len() {
        std::mem::swap(&mut vec[i], unsafe { &mut *(buffer[i].as_mut_ptr()) });
    }
}

impl<K: fmt::Debug + Ord + PartialEq, V: fmt::Debug> fmt::Debug for FrozenFlattenedVecMap<K, V> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut debug_map = f.debug_map();

        for (key, range) in self.keys.iter().zip(self.value_ranges.iter()) {
            debug_map.entry(
                key,
                &self.flattened_values[range.clone()]
                    .iter()
                    .collect::<Vec<&V>>(),
            );
        }

        debug_map.finish()
    }
}
