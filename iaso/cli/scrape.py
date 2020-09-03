import json
import os
import socket

from pathlib import Path

import click

from ..click.chrome import ChromeChoice
from ..click.coroutine import coroutine
from ..click.docker import DockerPathExists, docker_chrome_path, wrap_docker
from ..click.lazy import lazy_import

lazy_import(
    globals(),
    """
from ..environment import collect_environment_description

from ..scraping import scrape_resources
from ..scraping.jobs import ScrapingJobs
from ..scraping.jobs.resume import filter_completed_jobs
""",
)


@click.command()
@click.pass_context
@click.argument(
    "jobs",
    type=click.Path(
        exists=DockerPathExists(), readable=True, dir_okay=False, allow_dash=True
    ),
)
@click.argument(
    "dump",
    type=click.Path(
        exists=DockerPathExists(), readable=True, writable=True, file_okay=False
    ),
)
@click.option(
    "--resume",
    is_flag=True,
)
@click.option(
    "--proxy",
    type=ChromeChoice(),
    default="launch",
    show_envvar=True,
)
@click.option(
    "--chrome",
    type=click.Path(exists=DockerPathExists(), readable=True, dir_okay=False),
    default=docker_chrome_path,
)
@click.option(
    "--workers",
    type=click.IntRange(min=1),
    default=32,
    show_envvar=True,
)
@click.option(
    "--timeout",
    type=click.IntRange(min=5),
    default=30,
    show_envvar=True,
)
@click.option(
    "--log",
    type=click.Choice(["null", "stderr", "scrape.log"]),
    default="scrape.log",
    show_envvar=True,
)
@wrap_docker()
@coroutine
async def scrape(ctx, jobs, dump, resume, proxy, chrome, workers, timeout, log):
    """
    Runs the data scraping pipeline to gather information on the jobs
    defined in the JOBS file and stores them inside the DUMP folder.

    --resume allows you to resume a previously (partially) run scraping job.
    Otherwise, the DUMP folder will be cleared of any existing files or folders.

    \b
    --proxy launch launches a new proxy instance at a free port and closes
    it automatically after the scraping has finished. It uses the same proxy
    that can be launched using:
    > cmd-iaso proxy3 --port FREE_PORT --timeout TIMEOUT / 3
    --proxy launch is the default setting, which will implicitly discard
    the proxy's log.

    --proxy IPv4:PORT / --localhost IPv6:PORT / --proxy localhost:PORT connects
    to a running proxy instance at the specified address. The proxy will not
    automatically be closed after the scraping has finished.

    --chrome specifies the path to the Chrome browser executable.
    If not specified, the Chromium browser shipped with pyppeteer will be used instead.

    --workers specifies the number of concurrent processes to launch to work
    on scraping requests. A value of 1 is equivalent to running the scraping
    sequentially, while higher values can pipeline the scraping and increase
    the throughput drastically. It is recommended not to pick a very large value
    as the proxy might otherwise be overwhelmed and some requests might time out.
    By default, 32 workers are used.

    --timeout specifies the timeout in seconds that will be used to cull
    unresponsive scraping requests. Setting a larger value allows slower websites
    to load, especially dynamically loaded websites using JavaScript to provide
    their content. The timeout is also used to cull left-over processes.
    By default, a timeout of 30 seconds is used.

    --log specifies which logging output to use. 'null' discards all messages,
    'stderr' redirects them to stderr and 'scrape.log' appends them to the
    scrape.log file in the current working directory. By default, all messages
    are appended to scrape.log.
    """
    if not resume and os.listdir(dump):
        click.confirm(
            f"{dump} already contains files. Do you want to continue and clear all files in {dump}?",
            abort=True,
        )

        for subdir, dirs, files in os.walk(dump, topdown=False):
            subdir = Path(subdir)

            for dirc in dirs:
                os.rmdir(subdir / dirc)

            for file in files:
                os.remove(subdir / file)
    elif resume and not (Path(dump) / "PROGRESS").exists():
        raise click.UsageError(
            click.style(
                f"You cannot use --resume here as {dump} does not contain a progress report.",
                fg="red",
            )
        )

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if proxy != "launch":
        try:
            ip_address, _, port = proxy.rpartition(":")

            s.connect((ip_address, int(port)))
            s.settimeout(timeout)
            s.shutdown(socket.SHUT_RDWR)
        except:
            raise click.UsageError(
                f"network error: could not connect to proxy at {proxy}."
            )
        finally:
            s.close()

    with click.open_file(Path(dump) / "ENVIRONMENT", "w") as file:
        environment = collect_environment_description()
        environment[
            "cmd"
        ] = f"scrape {jobs} {dump} --proxy {proxy} --workers {workers} --timeout {timeout}"

        json.dump(environment, file)

    click.echo(f"Loading the scraping jobs from {jobs} ...")

    jobs = ScrapingJobs(jobs)
    total_jobs = len(jobs)

    if resume:
        jobs = filter_completed_jobs(jobs, Path(dump) / "PROGRESS")

    await scrape_resources(
        jobs,
        total_jobs,
        dump,
        proxy if proxy != "launch" else None,
        chrome,
        workers,
        timeout,
        log,
    )
