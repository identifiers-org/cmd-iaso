import gzip
import json
import os
import pickle
import re

from pathlib import Path

from tqdm import tqdm

from ..environment import collect_environment_description

pattern = r"pings_(\d+)\.gz"
matcher = re.compile(pattern)


def generate_datamine_from_dump(dump, datamine_path):
    providers = []
    errors = {}

    for subdir, dirs, files in os.walk(dump):
        subdir = Path(subdir)

        for filename in tqdm(files, desc="Combining scraping dumps"):
            result = matcher.match(filename)

            if result is None:
                continue

            rid = int(result.group(1))

            try:
                pings = []

                with gzip.open(subdir / filename, "rb") as file:
                    while True:
                        try:
                            pings.append(pickle.load(file))
                        except EOFError:
                            break

                pings = [
                    {
                        k: v
                        for k, v in ping.items()
                        if k not in ["content", "content-type"]
                    }
                    for ping in pings
                ]
            except Exception as err:
                errors[subdir / filename] = err

                continue

            provider = {
                "id": rid,
                "pings": pings,
            }

            providers.append(provider)

        break

    datamine = {
        "environment": collect_environment_description(),
        "providers": providers,
    }

    with gzip.open(datamine_path, "wt") as file:
        json.dump(datamine, file)

    return errors
