import asyncio
import multiprocessing as mp
import signal
import time

from tempfile import TemporaryDirectory

import psutil

from filelock import FileLock
from tqdm import tqdm

from .worker import fetch_resource_worker


async def scrape_resources_pool(
    ctx,
    dump,
    tempdir,
    proxy,
    proxy_address,
    chrome,
    jobs,
    total_jobs,
    workers,
    timeout,
    log,
):
    coordinating_processes = set([proxy]) if proxy is not None else set()

    scraping_pings_lock = tempdir / "pings.lock"

    with tqdm(initial=(total_jobs - len(jobs)), total=total_jobs) as progress:
        processes_timeout = dict()
        cleanup_timeout = dict()
        processes_tempdir = dict()

        final_timeout = [time.time() - 1]

        try:

            def signal_handler(signal, frame):
                final_timeout[0] = time.time() + timeout * 4
                jobs.clear()

                print()
                print("Shutting down the scraping worker pool ...")
                print("Waiting for all running workers to complete ...")
                print()

            signal.signal(signal.SIGINT, signal_handler)

            while len(jobs) > 0 or (
                len(processes_timeout) > 0 and time.time() < final_timeout[0]
            ):
                active_processes = set(mp.active_children()).difference(
                    coordinating_processes
                )

                finished_processes = []

                with FileLock(scraping_pings_lock):
                    for process, ptimeout in processes_timeout.items():
                        if process not in active_processes:
                            pass
                        elif time.time() > ptimeout:
                            process.kill()
                        else:
                            continue

                        finished_processes.append(process)

                for _ in range(min(workers - len(active_processes), len(jobs))):
                    try:
                        rid, lui, random, url = jobs.pop()
                    except IndexError:
                        break

                    worker_tempdir = TemporaryDirectory(dir=tempdir)

                    process = ctx.Process(
                        target=fetch_resource_worker,
                        args=(
                            dump,
                            proxy_address,
                            chrome,
                            timeout,
                            worker_tempdir.name,
                            scraping_pings_lock,
                            log,
                            rid,
                            lui,
                            random,
                            url,
                        ),
                    )

                    processes_timeout[process] = time.time() + timeout * 3
                    processes_tempdir[process] = worker_tempdir

                    process.start()

                    if len(jobs) == 0:
                        final_timeout[0] = time.time() + timeout * 4

                for process in finished_processes:
                    try:
                        for child in psutil.Process(pid=process.pid).children(
                            recursive=True
                        ):
                            try:
                                child.kill()
                            except:
                                pass
                    except:
                        pass

                    processes_tempdir.pop(process).cleanup()
                    processes_timeout.pop(process)

                    progress.update(1)

                child_pids = set(
                    process.pid for process in psutil.Process().children(recursive=True)
                ).difference(process.pid for process in coordinating_processes)

                active_pids = set(psutil.pids())

                progress.set_postfix(
                    {
                        "workers": len(processes_timeout),
                        "processes": len(cleanup_timeout),
                    }
                )

                finished_processes = []

                with FileLock(scraping_pings_lock):
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
        finally:
            # Final cleanup of processes
            with FileLock(scraping_pings_lock):
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
