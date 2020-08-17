import os
import re

from pathlib import Path

from tqdm import tqdm

from .dump2pings import dump2pings
from .tokenise import tokenise_pings
from .common_fragments import extract_common_fragments_per_lui
from .suffix_tree import extract_shared_suffix_tree
from .shared_fragments import extract_shared_fragments_from_tree

PINGS_PATTERN = re.compile(r"pings_(\d+)\.gz")


def analyse_dumped_information_content(dump_path):
    outer_progress = tqdm(position=0, desc="Analysing scraped resources")
    inner_progress = tqdm(position=1)

    for subdir, dirs, files in os.walk(dump_path):
        subdir = Path(subdir)

        outer_progress.reset(total=len(files))

        for filename in files:
            inner_progress.reset()

            result = PINGS_PATTERN.fullmatch(filename)

            if result is None:
                outer_progress.update()

                continue

            rid = int(result.group(1))

            outer_progress.set_postfix({"rid": rid})

            luis, tokens, https = tokenise_pings(
                inner_progress, dump2pings(subdir / filename)
            )

            luis, common_fragments_per_lui = extract_common_fragments_per_lui(
                inner_progress, luis, tokens, https
            )

            tree = extract_shared_suffix_tree(
                outer_progress, inner_progress, rid, luis, common_fragments_per_lui
            )

            shared_fragments = extract_shared_fragments_from_tree(
                outer_progress, inner_progress, rid, luis, tree
            )

            # TODO: calculate and store information metric

            outer_progress.update()

        break
