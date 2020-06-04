import asyncio
import multiprocessing as mp
import time

from pathlib import Path
from tempfile import TemporaryDirectory

import psutil

from filelock import FileLock
from tqdm import tqdm

from .worker import fetch_resource_worker


async def scrape_resources_pool(
    ctx, dump, proxy, proxy_address, chrome, jobs, workers, timeout
):
    coordinating_processes = set([proxy]) if proxy is not None else set()

    with TemporaryDirectory() as tempdir:
        dump = Path(dump)
        tempdir = Path(tempdir)

        with tqdm(total=len(jobs)) as progress:
            processes_timeout = dict()
            cleanup_timeout = dict()

            start_time = time.time()
            final_timeout = start_time - 1

            while len(jobs) > 0 or (
                (len(processes_timeout) > 0 or len(cleanup_timeout) > 0)
                and time.time() < final_timeout
            ):
                active_processes = set(mp.active_children()).difference(
                    coordinating_processes
                )

                finished_processes = []

                with FileLock(tempdir / "pings.lock"):
                    for process, ptimeout in processes_timeout.items():
                        if process not in active_processes:
                            pass
                        elif time.time() > ptimeout:
                            process.kill()
                        else:
                            continue

                        finished_processes.append(process)

                for _ in range(min(workers - len(active_processes), len(jobs))):
                    rid, lui, random, url = jobs.pop()

                    process = ctx.Process(
                        target=fetch_resource_worker,
                        args=(
                            dump,
                            proxy_address,
                            chrome,
                            timeout,
                            tempdir,
                            rid,
                            lui,
                            random,
                            url,
                        ),
                    )

                    processes_timeout[process] = time.time() + timeout * 3

                    process.start()

                    if len(jobs) == 0:
                        final_timeout = time.time() + timeout * 4

                for process in finished_processes:
                    processes_timeout.pop(process)

                    progress.update(1)

                child_pids = set(
                    process.pid for process in psutil.Process().children(recursive=True)
                ).difference(process.pid for process in coordinating_processes)

                active_pids = set(psutil.pids())

                progress.set_postfix(
                    {"child_pids": len(child_pids), "total_pids": len(active_pids)}
                )

                finished_processes = []

                with FileLock(tempdir / "pings.lock"):
                    for pid, ptimeout in cleanup_timeout.items():
                        if pid not in active_pids:
                            finished_processes.append(pid)
                        elif time.time() > ptimeout:
                            try:
                                psutil.Process(pid=pid).kill()
                            except:
                                pass

                for process in finished_processes:
                    cleanup_timeout.pop(process)

                for child in child_pids:
                    if child not in cleanup_timeout:
                        cleanup_timeout[child] = time.time() + timeout * 4

                await asyncio.sleep(0.1)

            # Final cleanup of processes
            with FileLock(tempdir / "pings.lock"):
                active_processes = set(mp.active_children()).difference(
                    coordinating_processes
                )

                for process, ptimeout in processes_timeout.items():
                    if process in active_processes:
                        process.kill()

                active_pids = set(psutil.pids())

                for pid, ptimeout in cleanup_timeout.items():
                    if pid in active_pids:
                        try:
                            psutil.Process(pid=pid).kill()
                        except:
                            pass
