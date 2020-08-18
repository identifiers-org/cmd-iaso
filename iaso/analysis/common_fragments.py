import gzip
import pickle
import re

from collections import defaultdict
from functools import partial
from multiprocessing import Pool

from athena import SharedFragmentTree, tokenise_and_join_with_spaces


def extract_common_fragments_per_lui_worker(filepath, entry_points, exclusions):
    tokens = []

    with open(filepath, "rb") as raw:
        for entry_point in entry_points:
            raw.seek(entry_point)

            with gzip.GzipFile(fileobj=raw, mode="rb") as file:
                ping = pickle.load(file)

                content = ping["content"]
                http = (
                    ping["redirects"][-1]["status"]
                    if len(ping["redirects"]) > 0
                    else None
                )

                if content is not None and http == 200:
                    tokens.append(
                        tokenise_and_join_with_spaces(content, exclusions).split(" ")
                    )

    if len(tokens) > 0:
        tree = SharedFragmentTree(tokens)

        return tree.extract_combination_of_all_common_fragments()
    else:
        return []


def extract_common_fragments_per_lui(inner_progress, filepath):
    inner_progress.set_description("Extracting lui entry points")
    inner_progress.reset(total=1)

    lui_entry_points = defaultdict(list)

    with open(filepath, "rb") as raw:
        entry_points = [m.start() for m in re.finditer(b"\x1f\x8b", raw.read())]

        for entry_point in entry_points:
            raw.seek(entry_point)

            try:
                with gzip.GzipFile(fileobj=raw, mode="rb") as file:
                    lui_entry_points[pickle.load(file)["lui"]].append(entry_point)
            except OSError:
                pass
            except Exception as err:
                pass

    extended_luis = set()

    for lui in lui_entry_points.keys():
        extended_luis.add(lui)

        if "#" in lui:
            extended_luis.add(lui[: lui.find("#")])

            for to in range(lui.find("#") + 1):
                if not lui[to].isalnum():
                    break

            extended_luis.add(lui[:to])

    exclusions = tuple(extended_luis)

    inner_progress.set_description("Extracting common token fragments")
    inner_progress.reset(total=len(lui_entry_points))

    common_fragments_per_lui = dict()

    def callback(lui, fragments):
        common_fragments_per_lui[lui] = fragments
        inner_progress.update()

    def error(err):
        raise err

    # TODO: need to handle ctrl-c and kill
    with Pool() as pool:
        for lui, entry_points in lui_entry_points.items():
            pool.apply_async(
                extract_common_fragments_per_lui_worker,
                (filepath, entry_points, exclusions),
                {},
                partial(callback, lui),
                error,
            )

        pool.close()
        pool.join()

    if len(common_fragments_per_lui) > 0:
        luis, common_fragments_per_lui = zip(*common_fragments_per_lui.items())
    else:
        luis, common_fragments_per_lui = [], []

    return luis, common_fragments_per_lui
