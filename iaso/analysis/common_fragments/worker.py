import gzip
import pickle
import re
import signal

from athena import SharedFragmentTree, tokenise_and_join_with_spaces


def extract_common_fragments_per_lui_worker(
    queue, lui, filepath, entry_points, exclusions
):
    signal.signal(signal.SIGINT, signal.SIG_IGN)

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

        fragments = tree.extract_combination_of_all_common_fragments()
    else:
        fragments = []

    queue.put((lui, fragments), True)
