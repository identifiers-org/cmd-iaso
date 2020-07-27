/*
Based on the Python suffix_trees module by Peter Us
https://github.com/ptrus/suffix-trees
Published under the MIT License
*/

use std::fmt;
use std::iter::FromIterator;
use tinyset::SetUsize as TinySet;
use vec_map::VecMap;

mod serde;

use super::OneShotGeneralisedSuffixTree;

pub type NodeRef = usize;

pub struct Node {
    pub index: usize,
    pub depth: usize,
    pub parent: NodeRef,
    pub transition_links: TinySet,
    pub generalised_indices: VecMap<TinySet>,
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

    pub fn fmt_rec(
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
