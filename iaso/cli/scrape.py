import json
import socket

from pathlib import Path

import click

from ..click.lazy import lazy_import
from ..click.docker import wrap_docker, DockerPathExists, docker_chrome_path
from ..click.coroutine import coroutine
from ..click.chrome import ChromeChoice

lazy_import(
    globals(),
    """
from ..environment import collect_environment_description

from ..scraping.jobs import ScrapingJobs
from ..scraping import scrape_resources
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
    "--proxy", type=ChromeChoice(), default="launch", show_envvar=True,
)
@click.option(
    "--chrome",
    type=click.Path(exists=DockerPathExists(), readable=True, dir_okay=False),
    default=docker_chrome_path,
)
@click.option(
    "--workers", type=click.IntRange(min=1), default=32, show_envvar=True,
)
@click.option(
    "--timeout", type=click.IntRange(min=5), default=30, show_envvar=True,
)
@wrap_docker()
@coroutine
async def scrape(ctx, jobs, dump, proxy, chrome, workers, timeout):
    """
    Runs the data scraping pipeline to gather information on the jobs
    defined in the JOBS file and stores them inside the DUMP folder.
    
    \b
    --proxy launch launches a new proxy instance at a free port and closes
    it automatically after the scraping has finished. It uses the same proxy
    that can be launched using:
    > cmd-iaso proxy3 --port FREE_PORT --timeout TIMEOUT / 3
    --proxy launch is the default setting.
    
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
    """
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

    await scrape_resources(
        ScrapingJobs(jobs),
        dump,
        proxy if proxy != "launch" else None,
        chrome,
        workers,
        timeout,
    )
