import gzip
import json
import os
import pickle
import re

from collections import defaultdict
from pathlib import Path

import click

from tqdm import tqdm

from .analysis.dump2pings import dump2pings

pattern = r"pings_(\d+)\.gz"
matcher = re.compile(pattern)


def generate_datamine_from_dump(dump, datamine_path):
    if not os.path.exists(Path(dump) / "ENVIRONMENT"):
        raise click.UsageError(f"No ENVIRONMENT file could be found in DUMP {dump}.")

    with open(Path(dump) / "ENVIRONMENT", "r") as file:
        environment = json.load(file)

    providers = []
    errors = defaultdict(list)

    for subdir, dirs, files in os.walk(dump):
        subdir = Path(subdir)

        for filename in tqdm(files, desc="Combining scraping dumps"):
            result = matcher.fullmatch(filename)

            if result is None:
                continue

            rid = int(result.group(1))

            pings = [
                {k: v for k, v in ping.items() if k not in ["content", "content-type"]}
                for ping in dump2pings(subdir / filename, errors=errors)
            ]

            provider = {
                "id": rid,
                "pings": pings,
            }

            providers.append(provider)

        break

    datamine = {
        "environment": environment,
        "providers": providers,
    }

    with gzip.open(datamine_path, "wt") as file:
        json.dump(datamine, file)

    return errors
