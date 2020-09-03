def extract_shared_fragments_from_tree(outer_progress, inner_progress, rid, luis, tree):
    if tree is not None:
        inner_progress.reset(total=len(luis))
    else:
        inner_progress.reset()

    inner_progress.set_description("Extracting shared fragments")

    if tree is None:
        return None

    inner_progress.reset(total=len(luis))

    outer_progress.set_postfix(
        {
            "rid": rid,
            "num_frags": len(luis),
            "avg_len": int((tree.size - len(tree)) / len(luis)),
        }
    )

    shared_fragments = tree.extract_all_shared_fragments_for_all_strings_parallel(
        progress=inner_progress.update
    )

    return shared_fragments
