/*
Based on the Python suffix_trees module by Peter Us
https://github.com/ptrus/suffix-trees
Published under the MIT License
*/

use std::collections::HashMap;

use super::utils::{compute_slink, create_leaf, create_node};
use super::{Node, NodeRef};

pub fn build_mc_creight<'a>(slab: &mut Vec<Node>, /*x*/ word: &'a [String], root: NodeRef) {
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
            u_ref = create_node(
                slab,
                &mut transition_links,
                &mut suffix_links,
                word,
                u_ref,
                d,
            );
        }

        create_leaf(
            slab,
            &mut transition_links,
            &mut suffix_links,
            word,
            i,
            u_ref,
            d,
        );

        // Check if !suffix_links.contains_key(u_ref)
        if suffix_links[u_ref] == std::usize::MAX {
            compute_slink(slab, &mut transition_links, &mut suffix_links, word, u_ref);
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
