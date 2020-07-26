use bit_set::BitSet;
use bit_vec::BitVec;
use serde::de::{self, Deserialize, Deserializer, SeqAccess, Visitor};
use serde::ser::{Serialize, SerializeTuple, Serializer};
use std::collections::HashMap;
use std::fmt;
use std::iter::FromIterator;
use std::ops::Index;
use tinyset::SetUsize as TinySet;
use vec_map::VecMap;

type NodeRef = usize;

#[derive(Hash, Eq, PartialEq, Debug)]
pub struct WordString(Vec<String>);

impl WordString {
    pub fn new() -> WordString {
        WordString(vec![])
    }

    pub fn len(&self) -> usize {
        self.0.len()
    }
}

impl Serialize for WordString {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        self.0.serialize(serializer)
    }
}

impl<'de> Deserialize<'de> for WordString {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        Vec::<String>::deserialize(deserializer).map(|words| WordString(words))
    }
}

impl From<Vec<String>> for WordString {
    fn from(vec: Vec<String>) -> WordString {
        WordString(vec)
    }
}

impl From<Vec<&str>> for WordString {
    fn from(vec: Vec<&str>) -> WordString {
        WordString(vec.into_iter().map(|s| String::from(s)).collect())
    }
}

impl From<&[String]> for WordString {
    fn from(slice: &[String]) -> WordString {
        WordString(slice.to_vec())
    }
}

impl Into<Vec<String>> for WordString {
    fn into(self) -> Vec<String> {
        self.0
    }
}

impl IntoIterator for WordString {
    type Item = String;
    type IntoIter = std::vec::IntoIter<Self::Item>;

    fn into_iter(self) -> Self::IntoIter {
        self.0.into_iter()
    }
}

impl<R> Index<R> for WordString
where
    Vec<String>: Index<R>,
{
    type Output = <Vec<String> as Index<R>>::Output;

    fn index(&self, index: R) -> &Self::Output {
        &self.0[index]
    }
}

struct Node {
    index: usize,
    depth: usize,
    parent: NodeRef,
    transition_links: TinySet,
    generalised_indices: VecMap<TinySet>,
}

impl Serialize for Node {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut tuple = serializer.serialize_tuple(5)?;

        tuple.serialize_element(&self.index)?;
        tuple.serialize_element(&self.depth)?;
        tuple.serialize_element(&self.parent)?;
        tuple.serialize_element(&self.transition_links.iter().collect::<Vec<usize>>())?;
        tuple.serialize_element(
            &self
                .generalised_indices
                .iter()
                .map(|(key, value)| (key, value.iter().collect::<Vec<usize>>()))
                .collect::<Vec<(usize, Vec<usize>)>>(),
        )?;

        tuple.end()
    }
}

impl<'de> Deserialize<'de> for Node {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct NodeVisitor;

        impl<'de> Visitor<'de> for NodeVisitor {
            type Value = Node;

            fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                formatter.write_str("struct Node")
            }

            fn visit_seq<V>(self, mut seq: V) -> Result<Self::Value, V::Error>
            where
                V: SeqAccess<'de>,
            {
                let index = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(0, &self))?;
                let depth = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(1, &self))?;
                let parent = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(2, &self))?;
                let transition_links: Vec<usize> = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(3, &self))?;
                let generalised_indices: Vec<(usize, Vec<usize>)> = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(4, &self))?;

                Ok(Node {
                    index,
                    depth,
                    parent,
                    transition_links: TinySet::from_iter(transition_links.into_iter()),
                    generalised_indices: VecMap::from_iter(
                        generalised_indices
                            .into_iter()
                            .map(|(key, value)| (key, TinySet::from_iter(value.into_iter()))),
                    ),
                })
            }
        }

        deserializer.deserialize_tuple(5, NodeVisitor)
    }
}

impl fmt::Debug for Node {
    fn fmt(&self, fmt: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt.debug_struct("Node")
            .field("index", &self.index)
            .field("depth", &self.depth)
            .field("parent", &self.parent)
            .field(
                "transition_links",
                &Vec::<usize>::from_iter(self.transition_links.iter()),
            )
            .field(
                "generalised_indices",
                &VecMap::<Vec<usize>>::from_iter(
                    self.generalised_indices
                        .iter()
                        .map(|(key, value)| (key, Vec::<usize>::from_iter(value.iter()))),
                ),
            )
            .finish()
    }
}

impl Node {
    pub fn new(
        slab: &mut Vec<Node>,
        index: usize,
        depth: usize,
        parent: Option<NodeRef>,
    ) -> NodeRef {
        let reference = slab.len();

        slab.push(Node {
            index,
            depth,
            parent: parent.unwrap_or(reference),
            transition_links: TinySet::new(),
            generalised_indices: VecMap::new(),
        });

        reference
    }

    fn fmt_rec(
        &self,
        tree: &OneShotGeneralisedSuffixTree,
        indent: usize,
        fmt: &mut fmt::Formatter<'_>,
    ) -> fmt::Result {
        fmt.write_fmt(format_args!(
            "Node {{ index: {:?} depth: {:?} generalised_indices: {:?} transition_links: [",
            self.index,
            self.depth,
            VecMap::<Vec<usize>>::from_iter(
                self.generalised_indices
                    .iter()
                    .map(|(key, value)| (key, Vec::<usize>::from_iter(value.iter())))
            )
        ))?;

        if !self.transition_links.is_empty() {
            fmt.write_str("\n")?;

            for child_ref in self.transition_links.iter() {
                let child = &tree.nodes[child_ref];

                fmt.write_fmt(format_args!("{:>indent$}", "", indent = (indent + 2)))?;
                fmt.write_fmt(format_args!(
                    "{} ({}) => ",
                    tree.word[child.index], child_ref
                ))?;

                child.fmt_rec(tree, indent + 2, fmt)?;

                fmt.write_str(",\n")?;
            }

            fmt.write_fmt(format_args!("{:>indent$}] }}", "", indent = indent))
        } else {
            fmt.write_str("] }}")
        }
    }
}

pub struct AllAnySet {
    all: BitSet,
    any: BitSet,

    primary_index: usize,
}

impl AllAnySet {
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

    fn subset(&self, other: &VecMap<TinySet>) -> Option<AllAnySet> {
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

        return Some(AllAnySet {
            all: self.all.clone(),
            any: new_any,

            primary_index: self.primary_index,
        });
    }
}

pub struct OneShotGeneralisedSuffixTree {
    nodes: Vec<Node>,
    root_ref: NodeRef,

    word: WordString,
    word_starts: Vec<usize>,
}

impl Serialize for OneShotGeneralisedSuffixTree {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut tuple = serializer.serialize_tuple(4)?;

        tuple.serialize_element(&self.nodes)?;
        tuple.serialize_element(&self.root_ref)?;
        tuple.serialize_element(&self.word)?;
        tuple.serialize_element(&self.word_starts)?;

        tuple.end()
    }
}

impl<'de> Deserialize<'de> for OneShotGeneralisedSuffixTree {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct OneShotGeneralisedSuffixTreeVisitor;

        impl<'de> Visitor<'de> for OneShotGeneralisedSuffixTreeVisitor {
            type Value = OneShotGeneralisedSuffixTree;

            fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                formatter.write_str("struct OneShotGeneralisedSuffixTree")
            }

            fn visit_seq<V>(self, mut seq: V) -> Result<Self::Value, V::Error>
            where
                V: SeqAccess<'de>,
            {
                let nodes = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(0, &self))?;
                let root_ref = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(1, &self))?;
                let word = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(2, &self))?;
                let word_starts = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(3, &self))?;

                Ok(OneShotGeneralisedSuffixTree {
                    nodes,
                    root_ref,

                    word,
                    word_starts,
                })
            }
        }

        deserializer.deserialize_tuple(4, OneShotGeneralisedSuffixTreeVisitor)
    }
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
    pub fn new(input: Vec<WordString>) -> OneShotGeneralisedSuffixTree {
        let mut nodes = Vec::new();

        let root_ref = Node::new(&mut nodes, 0, 0, None);
        assert_eq!(root_ref, 0);

        let terminals = OneShotGeneralisedSuffixTree::terminal_symbols_generator();
        assert_eq!(terminals.len() >= input.len(), true);

        let mut words: Vec<String> = Vec::with_capacity(input.len() * 2);
        let mut word_starts: Vec<usize> = Vec::with_capacity(input.len());

        // Add terminals and calculate word starts
        for (x, t) in input.into_iter().zip(terminals.into_iter()) {
            word_starts.push(words.len());

            words.extend(x.into_iter());
            words.push(t);
        }

        words.shrink_to_fit();
        let word = WordString::from(words);

        OneShotGeneralisedSuffixTree::build_mc_creight(&mut nodes, &word[..], root_ref);

        let mut generalised_indices: Vec<VecMap<TinySet>> = Vec::with_capacity(nodes.len());
        generalised_indices.resize_with(nodes.len(), || VecMap::new());

        if !word_starts.is_empty() {
            // Label the generalised suffix tree nodes
            let mut stack: Vec<(NodeRef, bool)> = vec![(root_ref, true)];

            while let Some((node_ref, push)) = stack.pop() {
                let node = &nodes[node_ref];

                if !generalised_indices[node_ref].is_empty() {
                    continue;
                };

                if node.transition_links.is_empty() {
                    // node is a leaf
                    let start = match word_starts.binary_search(&node.index) {
                        Ok(idx) => idx,
                        Err(idx) => idx - 1,
                    };

                    generalised_indices[node_ref]
                        .entry(start)
                        .or_insert_with(|| TinySet::new())
                        .insert(node.index - word_starts[start]);
                } else if push {
                    stack.push((node_ref, false));

                    for child_ref in node.transition_links.iter() {
                        stack.push((child_ref, true));
                    }
                } else {
                    for child_ref in node.transition_links.iter() {
                        // We need to borrow two entries from generalised_indices mutabably
                        let (node_indices, child_indices) = if node_ref < child_ref {
                            let (node_half, child_half) =
                                generalised_indices.split_at_mut(child_ref);

                            (&mut node_half[node_ref], &mut child_half[0])
                        } else {
                            let (child_half, node_half) =
                                generalised_indices.split_at_mut(node_ref);

                            (&mut node_half[0], &mut child_half[child_ref])
                        };

                        for (n, indices) in child_indices.iter() {
                            let union_indices =
                                node_indices.entry(n).or_insert_with(|| TinySet::new());

                            for index in indices.iter() {
                                union_indices.insert(index);
                            }
                        }
                    }
                }
            }
        }

        for (node_ref, generalised_indices) in generalised_indices.into_iter().enumerate() {
            nodes[node_ref].generalised_indices = generalised_indices;
        }

        OneShotGeneralisedSuffixTree {
            nodes,
            root_ref,

            word,
            word_starts,
        }
    }

    fn build_mc_creight<'a>(slab: &mut Vec<Node>, /*x*/ word: &'a [String], root: NodeRef) {
        /*
        Builds a Suffix tree using McCreight O(n) algorithm.

        Algorithm based on:
        McCreight, Edward M. "A space-economical suffix tree construction algorithm." - ACM, 1976.
        Implementation based on:
        UH CS - 58093 String Processing Algorithms Lecture Notes
        */

        let mut transition_links: Vec<HashMap<&'a [String], NodeRef>> = vec![HashMap::new()];
        let mut suffix_links: Vec<NodeRef> = vec![root];

        let mut u_ref: NodeRef = root;
        let mut d: usize = 0;

        for i in 0..word.len() {
            let mut u = &slab[u_ref];

            while u.depth == d
                && transition_links[u_ref].contains_key(std::slice::from_ref(&word[d + i]))
            {
                u_ref = transition_links[u_ref][std::slice::from_ref(&word[d + i])];
                d += 1;
                u = &slab[u_ref];

                while d < u.depth && word[u.index + d] == word[i + d] {
                    d += 1;
                }
            }

            if d < u.depth {
                u_ref = OneShotGeneralisedSuffixTree::create_node(
                    slab,
                    &mut transition_links,
                    &mut suffix_links,
                    word,
                    u_ref,
                    d,
                );
            }

            OneShotGeneralisedSuffixTree::create_leaf(
                slab,
                &mut transition_links,
                &mut suffix_links,
                word,
                i,
                u_ref,
                d,
            );

            if suffix_links[u_ref] == std::usize::MAX {
                // !suffix_links.contains_key(u_ref)
                OneShotGeneralisedSuffixTree::compute_slink(
                    slab,
                    &mut transition_links,
                    &mut suffix_links,
                    word,
                    u_ref,
                );
            }

            u_ref = suffix_links[u_ref];

            d = d.saturating_sub(1);
        }

        for (node, transition_links) in slab.iter_mut().zip(transition_links.into_iter()) {
            for link in transition_links.values() {
                node.transition_links.insert(*link);
            }
        }
    }

    fn create_node<'a>(
        slab: &mut Vec<Node>,
        transition_links: &mut Vec<HashMap<&'a [String], NodeRef>>,
        suffix_links: &mut Vec<NodeRef>,
        /*x*/ word: &'a [String],
        /*u*/ child_ref: NodeRef,
        /*d*/ depth: usize,
    ) -> NodeRef {
        let child = &slab[child_ref];
        let index = child.index;
        let parent_ref = child.parent;

        let node_ref = Node::new(slab, index, depth, Some(parent_ref));
        transition_links.push(HashMap::new());
        suffix_links.push(std::usize::MAX);

        transition_links[node_ref].insert(std::slice::from_ref(&word[index + depth]), child_ref);

        let child = &mut slab[child_ref];
        child.parent = node_ref;

        let parent = &mut slab[parent_ref];
        transition_links[parent_ref]
            .insert(std::slice::from_ref(&word[index + parent.depth]), node_ref);

        node_ref
    }

    fn create_leaf<'a>(
        slab: &mut Vec<Node>,
        transition_links: &mut Vec<HashMap<&'a [String], NodeRef>>,
        suffix_links: &mut Vec<NodeRef>,
        /*x*/ word: &'a [String],
        /*i*/ index: usize,
        /*u*/ parent_ref: NodeRef,
        /*d*/ depth: usize,
    ) -> NodeRef {
        let leaf_ref = Node::new(slab, index, word.len() - index, Some(parent_ref));
        transition_links.push(HashMap::new());
        suffix_links.push(std::usize::MAX);

        transition_links[parent_ref].insert(std::slice::from_ref(&word[index + depth]), leaf_ref);

        leaf_ref
    }

    fn compute_slink<'a>(
        slab: &mut Vec<Node>,
        transition_links: &mut Vec<HashMap<&'a [String], NodeRef>>,
        suffix_links: &mut Vec<NodeRef>,
        /*x*/ word: &'a [String],
        /*u*/ u_ref: NodeRef,
    ) {
        let u = &slab[u_ref];

        let depth = u.depth;

        let mut v_ref = suffix_links[u.parent];
        let mut v = &slab[v_ref];

        while v.depth < (depth - 1) {
            v_ref = transition_links[v_ref][std::slice::from_ref(&word[u.index + v.depth + 1])];
            v = &slab[v_ref];
        }

        if v.depth > (depth - 1) {
            v_ref = OneShotGeneralisedSuffixTree::create_node(
                slab,
                transition_links,
                suffix_links,
                word,
                v_ref,
                depth - 1,
            );
        }

        suffix_links[u_ref] = v_ref;
    }

    fn terminal_symbols_generator() -> Vec<String> {
        (0xE000..=0xF8FF)
            .chain(0xF0000..=0xFFFFD)
            .chain(0x100000..=0x10FFFD)
            .filter_map(|code| std::char::from_u32(code))
            .map(|c| {
                let mut s = String::with_capacity(1);
                s.push(c);
                s
            })
            .collect()
    }

    fn find_longest_common_substring_per_index(
        &self,
        node_ref: NodeRef,
        string_indices: AllAnySet,
        index_lengths: &mut Vec<usize>,
    ) {
        let node = &self.nodes[node_ref];

        for start in node.generalised_indices[string_indices.primary_index].iter() {
            // Exclude the start of the separator of the primary string
            if start < index_lengths.len() {
                index_lengths[start] = usize::max(index_lengths[start], node.depth);
            }
        }

        for child_ref in node.transition_links.iter() {
            if let Some(string_sub_indices) =
                string_indices.subset(&self.nodes[child_ref].generalised_indices)
            {
                self.find_longest_common_substring_per_index(
                    child_ref,
                    string_sub_indices,
                    index_lengths,
                )
            };
        }
    }

    fn no_early_stop(_: usize, _: &mut Vec<(WordString, usize)>) -> bool {
        false
    }

    pub fn extract_longest_common_non_overlapping_substrings(
        &self,
        string_indices: AllAnySet,
        early_stop: Option<&mut dyn FnMut(usize, &mut Vec<(WordString, usize)>) -> bool>,
        debug: bool,
    ) -> Vec<(WordString, usize)> {
        let primary_length = (if (string_indices.primary_index + 1) >= self.word_starts.len() {
            self.word.len()
        } else {
            self.word_starts[string_indices.primary_index + 1]
        }) - self.word_starts[string_indices.primary_index]
            - 1;

        if primary_length == 0 {
            return vec![];
        };

        let no_early_stop = &mut OneShotGeneralisedSuffixTree::no_early_stop;

        let early_stop: &mut dyn FnMut(usize, &mut Vec<(WordString, usize)>) -> bool =
            match early_stop {
                Some(early_stop) => early_stop,
                None => no_early_stop,
            };

        let mut index_lengths = Vec::with_capacity(primary_length);
        index_lengths.resize(primary_length, 0);

        let offset = self.word_starts[string_indices.primary_index];

        self.find_longest_common_substring_per_index(
            self.root_ref,
            string_indices,
            &mut index_lengths,
        );

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

            while i < substrings.len()
                && substrings[i].0 >= longest_non_overlapping_substring_length
            {
                let start = substrings[i].1;

                if !remaining_string.contains(start) {
                    substrings.remove(i);
                    i = i.wrapping_sub(1);
                    continue;
                }

                if !remaining_string.contains(start + longest_non_overlapping_substring_length - 1)
                {
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
                        &self.word[(offset + start)
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
                || (i < substrings.len()
                    && substrings[i].0 < longest_non_overlapping_substring_length)
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

    pub fn len(&self) -> usize {
        self.word_starts.len()
    }

    pub fn is_empty(&self) -> bool {
        self.word_starts.is_empty()
    }

    pub fn size(&self) -> usize {
        self.word.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn system_test() {
        let strings = vec![
            WordString::from(vec!["a", "b", "c", "d", "e"]),
            WordString::from(vec!["a", "b", "c"]),
            WordString::from(vec!["c", "d", "e"]),
            WordString::from(vec!["b", "c"]),
        ];

        let tree = match OneShotGeneralisedSuffixTree::new(strings) {
            Ok(tree) => tree,
            Err(err) => panic!(format!("{:?}", err)),
        };

        let string_indices = match AllAnySet::new(BitSet::from_iter(0..1), BitSet::from_iter(1..4))
        {
            Ok(string_indices) => string_indices,
            Err(err) => panic!(format!("{:?}", err)),
        };

        let lcnosss =
            tree.extract_longest_common_non_overlapping_substrings(string_indices, None, false);

        assert_eq!(
            lcnosss,
            vec![
                (WordString::from(vec!["c", "d", "e"]), 2),
                (WordString::from(vec!["a", "b"]), 0)
            ]
        );
    }
}
