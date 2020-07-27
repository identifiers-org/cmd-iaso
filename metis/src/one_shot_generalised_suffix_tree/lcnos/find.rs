use super::{AllAnySet, Node, NodeRef};

pub fn find_longest_common_substring_per_index(
    nodes: &[Node],
    node_ref: NodeRef,
    string_indices: AllAnySet,
    index_lengths: &mut [usize],
) {
    let node = &nodes[node_ref];

    for start in node.generalised_indices[string_indices.primary_index()].iter() {
        // Exclude the start of the separator of the primary string
        if start < index_lengths.len() {
            index_lengths[start] = usize::max(index_lengths[start], node.depth);
        }
    }

    for child_ref in node.transition_links.iter() {
        if let Some(string_sub_indices) =
            string_indices.subset(&nodes[child_ref].generalised_indices)
        {
            find_longest_common_substring_per_index(
                nodes,
                child_ref,
                string_sub_indices,
                index_lengths,
            )
        };
    }
}
