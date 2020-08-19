import gzip
import multiprocessing as mp
import os
import pickle
import re
import signal
import time

from collections import defaultdict
from queue import Empty as EmptyQueueException

from .worker import extract_common_fragments_per_lui_worker


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

    workers = os.cpu_count() or 1

    jobs = list(lui_entry_points.items())

    running_processes = set()
    queue = mp.Queue()

    try:

        def signal_handler(signal, frame):
            jobs.clear()

            print()
            print("Shutting down the common fragments worker pool ...")
            print("Waiting for all running workers to complete ...")
            print()

        signal.signal(signal.SIGINT, signal_handler)

        while len(jobs) > 0 or len(running_processes) > 0:
            active_processes = set(mp.active_children())

            inner_progress.set_postfix({"workers": len(active_processes)})

            finished_processes = []

            for process in running_processes:
                if process not in active_processes:
                    finished_processes.append(process)

            for _ in range(min(workers - len(active_processes), len(jobs))):
                try:
                    lui, entry_points = jobs.pop()
                except IndexError:
                    break

                process = mp.Process(
                    target=extract_common_fragments_per_lui_worker,
                    args=(queue, lui, filepath, entry_points, exclusions),
                )

                running_processes.add(process)

                process.start()

            for process in finished_processes:
                running_processes.remove(process)

            while True:
                try:
                    lui, fragments = queue.get(False)

                    common_fragments_per_lui[lui] = fragments

                    inner_progress.update()
                except EmptyQueueException:
                    break

            time.sleep(0.01)
    finally:
        signal.signal(signal.SIGINT, signal.SIG_DFL)

    inner_progress.set_postfix(None)

    if len(common_fragments_per_lui) > 0:
        luis, common_fragments_per_lui = zip(*common_fragments_per_lui.items())
    else:
        luis, common_fragments_per_lui = [], []

    return luis, common_fragments_per_lui
