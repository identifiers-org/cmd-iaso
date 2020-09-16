import gzip
import json
import mmap
import os
import pickle
import re
import signal
import time

from collections import defaultdict
from pathlib import Path

import click

from tqdm import tqdm

PINGS_PATTERN = re.compile(r"pings_(\d+)\.gz")


def dump2pings(filepath, errors):
    with open(filepath, "r+b") as raw:
        with mmap.mmap(raw.fileno(), 0) as raw:
            entry_points = [m.start() for m in re.finditer(b"\x1f\x8b", raw)]

            for entry_point in entry_points:
                raw.seek(entry_point)

                try:
                    with gzip.GzipFile(fileobj=raw, mode="rb") as file:
                        yield pickle.load(file)
                except OSError:
                    pass
                except Exception as err:
                    errors[filepath].append(err)


def generate_datamine_from_dump(dump, datamine_path, analysis):
    if not os.path.exists(Path(dump) / "ENVIRONMENT"):
        raise click.UsageError(f"No ENVIRONMENT file could be found in DUMP {dump}.")

    if analysis:
        from .analysis import analyse_single_file

    with open(Path(dump) / "ENVIRONMENT", "r") as file:
        environment = json.load(file)

    with open(datamine_path, "w") as file:
        file.write('{"environment": ')
        json.dump(environment, file)
        file.write(', "providers": [')

        errors = defaultdict(list)

        append_provider = False

        for subdir, dirs, files in os.walk(dump):
            subdir = Path(subdir)

            outer_progress = tqdm(
                position=0,
                total=len(files),
                desc=(
                    "Combining "
                    + ("and Analysing " if analysis else "")
                    + "scraping dumps"
                ),
            )
            inner_progress = tqdm(position=1, desc="Loading scraped resource")

            analysis_interrupted = [False]

            def signal_handler(signal, frame):
                analysis_interrupted[0] = True

                print()
                print("Interrupting the dump2datamine command ...")
                print("Waiting for the current task to finish ...")
                print()

            signal.signal(signal.SIGINT, signal_handler)

            for i, filename in enumerate(files):
                inner_progress.set_description("Loading scraped resource")
                inner_progress.reset(total=1)

                result = PINGS_PATTERN.fullmatch(filename)

                if result is None:
                    continue

                rid = int(result.group(1))

                # Combining dump

                if append_provider:
                    file.write(", ")

                file.write(f'{{"id": {rid}, "pings": [')

                try:
                    append_ping = False

                    for ping in dump2pings(subdir / filename, errors=errors):
                        if append_ping:
                            file.write(", ")

                        ping["empty_content"] = ping.get("content", None) is None

                        ping.pop("content", None)
                        ping.pop("content-type", None)

                        json.dump(ping, file)

                        append_ping = True
                except StopIteration:
                    pass

                # Optional analysis

                file.write('], "analysis": ')

                if analysis:
                    analyse_single_file(
                        file, subdir, outer_progress, inner_progress, filename, rid
                    )
                else:
                    file.write("null")

                # Finishing datamine provider entry

                file.write("}")

                append_provider = True

                outer_progress.update()

                if analysis_interrupted[0]:
                    break

                if analysis:
                    time.sleep(1)

            break

        file.write("]}")

    return errors
