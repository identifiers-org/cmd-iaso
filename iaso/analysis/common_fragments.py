from collections import defaultdict
from functools import partial
from multiprocessing import Pool

from athena import SharedFragmentTree


def extract_common_fragments_per_lui_worker(ts):
    tree = SharedFragmentTree(ts)

    return tree.extract_combination_of_all_common_fragments()


def extract_common_fragments_per_lui(inner_progress, luis, tokens, https):
    inner_progress.reset(total=len(set(luis)))
    inner_progress.set_description("Extracting common fragments per LUI")

    tokens_per_lui_acc = defaultdict(list)

    for lui, t, http in zip(luis, tokens, https):
        tokens_per_lui_acc[lui].append((t, http))

    common_fragments_per_lui = dict()

    def callback(lui, fragments):
        common_fragments_per_lui[lui] = fragments
        inner_progress.update()

    def error(err):
        raise err

    with Pool() as pool:
        for lui, ts in tokens_per_lui_acc.items():
            if all((t is None) or (h != 200) for t, h in ts):
                common_fragments_per_lui[lui] = []
            else:
                ts = [t for t, h in ts if (t is not None) and (h == 200)]

                pool.apply_async(
                    extract_common_fragments_per_lui_worker,
                    (ts,),
                    {},
                    partial(callback, lui),
                    error,
                )

        pool.close()
        pool.join()

    luis, common_fragments_per_lui = zip(*common_fragments_per_lui.items())

    return luis, common_fragments_per_lui
