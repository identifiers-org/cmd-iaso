import gc
import json
import os
import re
import signal
import time

from functools import partial
from multiprocessing import Pipe, Process
from pathlib import Path

from tqdm import tqdm

from .common_fragments import extract_common_fragments_per_lui
from .shared_fragments import extract_shared_fragments_from_tree
from .suffix_tree import extract_shared_suffix_tree

PINGS_PATTERN = re.compile(r"pings_(\d+)\.gz")


class IPCProxy:
    def __init__(self, name, pipe):
        self.name = name
        self.pipe = pipe

    def __call_proxy(self, method, *args, **kwargs):
        self.pipe.send((self.name, method, args, kwargs))

    def __getattr__(self, attr):
        return partial(self.__call_proxy, attr)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.pipe.close()


def analyse_single_file_worker(outer_progress, inner_progress, filepath, rid, datamine):
    with outer_progress, inner_progress:
        outer_progress.set_postfix({"rid": rid})

        luis, common_fragments_per_lui = extract_common_fragments_per_lui(
            inner_progress, filepath
        )

        common_lengths = [len(fragments) for fragments in common_fragments_per_lui]
        common_noise = [
            fragments.count("NOISE") for fragments in common_fragments_per_lui
        ]

        gc.collect()

        tree = extract_shared_suffix_tree(
            outer_progress, inner_progress, rid, luis, common_fragments_per_lui
        )

        del common_fragments_per_lui

        gc.collect()

        shared_fragments = extract_shared_fragments_from_tree(
            outer_progress, inner_progress, rid, luis, tree
        )

        del tree

        gc.collect()

        datamine.write("[")

        append_analysis = False

        for l, (lui, fragments) in enumerate(zip(luis, shared_fragments)):
            L = common_lengths[l]

            if L == 0:
                continue

            C = sum(len(fragment) for fragment in fragments)
            n = len(fragments)

            info = (L - C + n - 1.0) / L

            if append_analysis:
                datamine.write(", ")

            json.dump(
                {
                    "lui": lui,
                    "information_content": round(info, 5),
                    "length": L,
                    "noise": common_noise[l],
                },
                datamine,
            )

            append_analysis = True

        datamine.write("]")


def analyse_single_file(
    datamine, subdir, outer_progress, inner_progress, filename, rid
):
    pipe_read, pipe_write = Pipe(False)

    process = Process(
        target=analyse_single_file_worker,
        args=(
            IPCProxy("outer_progress", pipe_write),
            IPCProxy("inner_progress", pipe_write),
            subdir / filename,
            rid,
            IPCProxy("datamine", pipe_write),
        ),
    )
    process.start()

    pipe_write.close()

    proxies = {
        "outer_progress": outer_progress,
        "inner_progress": inner_progress,
        "datamine": datamine,
    }

    while True:
        try:
            (proxy_name, method, args, kwargs) = pipe_read.recv()

            getattr(proxies[proxy_name], method)(*args, **kwargs)
        except EOFError:
            break

    inner_progress.set_description("Finalising resource analysis")
    inner_progress.reset(total=1)

    process.join()
