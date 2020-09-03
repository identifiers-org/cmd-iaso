from athena import SharedFragmentTree


def extract_shared_suffix_tree(
    outer_progress, inner_progress, rid, luis, common_fragments_per_lui
):
    inner_progress.set_description("Extracting shared suffix tree")
    inner_progress.reset(total=1)

    outer_progress.set_postfix(
        {
            "rid": rid,
            "num_luis": len(luis),
            "num_frags": sum(
                fragment.count("NOISE") + 1 for fragment in common_fragments_per_lui
            ),
            "avg_frag_len": sum(
                len(fragment) - fragment.count("NOISE")
                for fragment in common_fragments_per_lui
            )
            / sum(fragment.count("NOISE") + 1 for fragment in common_fragments_per_lui)
            if len(common_fragments_per_lui) > 0
            else 0.0,
        }
    )

    tree = (
        SharedFragmentTree(common_fragments_per_lui)
        if len(common_fragments_per_lui) > 0
        else None
    )

    outer_progress.set_postfix({"rid": rid})

    return tree
