/*
Based on the Python suffix_trees module by Peter Us
https://github.com/ptrus/suffix-trees
Published under the MIT License
*/

use tinyset::SetUsize as TinySet;
use vec_map::VecMap;

mod mc_creight;
mod utils;

use super::{Node, NodeRef, WordString};
use mc_creight::build_mc_creight;
use utils::terminal_symbols_generator;

pub fn build(input: Vec<WordString>) -> (Vec<Node>, NodeRef, WordString, Vec<usize>) {
    let mut nodes = Vec::new();

    let root_ref = Node::new(&mut nodes, 0, 0, None);
    assert_eq!(root_ref, 0);

    let terminals = terminal_symbols_generator();
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

    build_mc_creight(&mut nodes, &word[..], root_ref);

    let mut generalised_indices: Vec<VecMap<TinySet>> = Vec::with_capacity(nodes.len());
    generalised_indices.resize_with(nodes.len(), VecMap::new);

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
                    .or_insert_with(TinySet::new)
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
                        let (node_half, child_half) = generalised_indices.split_at_mut(child_ref);

                        (&mut node_half[node_ref], &mut child_half[0])
                    } else {
                        let (child_half, node_half) = generalised_indices.split_at_mut(node_ref);

                        (&mut node_half[0], &mut child_half[child_ref])
                    };

                    for (n, indices) in child_indices.iter() {
                        let union_indices = node_indices.entry(n).or_insert_with(TinySet::new);

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

    (nodes, root_ref, word, word_starts)
}
