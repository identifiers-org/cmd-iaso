import concurrent.futures
import gc
import os
import re
import time

from pathlib import Path

from tqdm import tqdm

from .dump2pings import dump2pings
from .tokenise import tokenise_pings
from .common_fragments import extract_common_fragments_per_lui
from .suffix_tree import extract_shared_suffix_tree
from .shared_fragments import extract_shared_fragments_from_tree

PINGS_PATTERN = re.compile(r"pings_(\d+)\.gz")


def analyse_single_file(filepath, rid, i, total):
    # TODO: This is recreating the progressbar for every task, maybe we can use message passing
    outer_progress = tqdm(
        position=0, total=total, initial=i, desc="Analysing scraped resources"
    )
    inner_progress = tqdm(position=1, desc="Loading scraped resources")

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

        for i, filename in enumerate(files[130:]):
            result = PINGS_PATTERN.fullmatch(filename)

            if result is None:
                continue

            rid = int(result.group(1))

            with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
                executor.submit(
                    analyse_single_file, subdir / filename, rid, i, len(files)
                ).result()

            time.sleep(1)

        break
