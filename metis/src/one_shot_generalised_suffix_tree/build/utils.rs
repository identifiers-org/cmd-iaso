/*
Based on the Python suffix_trees module by Peter Us
https://github.com/ptrus/suffix-trees
Published under the MIT License
*/

use std::collections::HashMap;

use super::{Node, NodeRef};

pub fn create_node<'a>(
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

pub fn create_leaf<'a>(
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

pub fn compute_slink<'a>(
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
        v_ref = create_node(slab, transition_links, suffix_links, word, v_ref, depth - 1);
    }

    suffix_links[u_ref] = v_ref;
}

pub fn terminal_symbols_generator() -> Vec<String> {
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
