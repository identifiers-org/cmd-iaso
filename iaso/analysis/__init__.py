import gc
import os
import re
import time

from functools import partial
from multiprocessing import Process, Pipe
from pathlib import Path

from tqdm import tqdm

from .dump2pings import dump2pings
from .tokenise import tokenise_pings
from .common_fragments import extract_common_fragments_per_lui
from .suffix_tree import extract_shared_suffix_tree
from .shared_fragments import extract_shared_fragments_from_tree

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


def analyse_single_file(outer_progress, inner_progress, filepath, rid):
    with outer_progress, inner_progress:
        outer_progress.set_postfix({"rid": rid})

        luis, tokens, https = tokenise_pings(inner_progress, dump2pings(filepath))

        luis, common_fragments_per_lui = extract_common_fragments_per_lui(
            inner_progress, luis, tokens, https
        )

        del tokens
        del https

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

        # TODO: calculate and store information metric


def analyse_dumped_information_content(dump_path):
    for subdir, dirs, files in os.walk(dump_path):
        subdir = Path(subdir)

        progress = {
            "outer_progress": tqdm(
                position=0, total=len(files), desc="Analysing scraped resources"
            ),
            "inner_progress": tqdm(position=1, desc="Loading scraped resource"),
        }

        for i, filename in enumerate(files[130:]):
            progress["inner_progress"].set_description("Loading scraped resource")
            progress["inner_progress"].reset(total=1)

            result = PINGS_PATTERN.fullmatch(filename)

            if result is None:
                continue

            rid = int(result.group(1))

            pipe_read, pipe_write = Pipe(False)

            process = Process(
                target=analyse_single_file,
                args=(
                    IPCProxy("outer_progress", pipe_write),
                    IPCProxy("inner_progress", pipe_write),
                    subdir / filename,
                    rid,
                ),
            )
            process.start()

            pipe_write.close()

            while True:
                try:
                    (progress_name, method, args, kwargs) = pipe_read.recv()

                    getattr(progress[progress_name], method)(*args, **kwargs)
                except EOFError:
                    break

            progress["inner_progress"].set_description("Finalising resource analysis")
            progress["inner_progress"].reset(total=1)

            process.join()

            time.sleep(1)

        break
