import asyncio
import json
import os
import socket

from functools import update_wrapper, partial
from pathlib import Path

import click

from dotenv import load_dotenv

load_dotenv(dotenv_path=(Path(".") / ".env"))

from . import curation

from .curation.session import CurationSession

from .curation.terminal import (
    TerminalController,
    TerminalNavigator,
    TerminalFormatter,
)
from .curation.pyppeteer import PyppeteerLauncher
from .curation.pyppeteer.controller import PyppeteerController
from .curation.pyppeteer.navigator import PyppeteerNavigator
from .curation.pyppeteer.informant import PyppeteerFormatter

from .scraping.http.proxy3 import serve as serve_proxy
from .scraping import scrape_resources

from .dump2datamine import generate_datamine_from_dump

from .click.validators import (
    load_registered_validators,
    validate_validators,
    list_validators,
)
from .click.mutex import ValidateMutex, MutexOption
from .click.chrome import ChromeChoice
from .click.docker import register_docker, DockerPathExists, wrap_docker

from .utils import format_json
from .environment import collect_environment_description
from .registry import Registry
from .datamine import Datamine
from .namespace_ids import NamespaceIds
from .scraping.jobs import ScrapingJobs
from .scraping.jobs.generate import generate_scraping_jobs


def coroutine(f):
    f = asyncio.coroutine(f)

    def wrapper(*args, **kwargs):
        ctx = click.get_current_context()
        ctx.obj["loop"] = asyncio.get_event_loop()
        return ctx.obj["loop"].run_until_complete(f(*args, **kwargs))

    return update_wrapper(wrapper, f)


def ctx_registry(ctx):
    registry = ctx.obj.get("registry")

    if registry is None:
        registry = Registry()
        ctx.obj["registry"] = registry

    return registry


def get_version():
    try:
        from importlib import metadata

        return metadata.version
    except ImportError:
        # Running on pre-3.8 Python
        import pkg_resources

        return pkg_resources.get_distribution("cmd-iaso").version


@click.group()
@click.version_option(version=get_version())
@click.pass_context
@click.option(
    "--docker",
    type=click.Path(exists=False),
    hidden=True,
    allow_from_autoenv=False,
    is_eager=True,
    callback=register_docker,
    expose_value=False,
)
def cli(ctx):
    ctx.ensure_object(dict)

    load_registered_validators(ctx)


@cli.command()
@click.pass_context
@wrap_docker()
def environment(ctx):
    """
    Pretty-prints a description of the current environment.
    """
    click.echo(format_json(collect_environment_description()))


@cli.command()
@click.pass_context
@wrap_docker()
def registry(ctx):
    """
    Pretty-prints the current status of the identifiers.org registry.
    """
    click.echo(format_json(ctx_registry(ctx)))


@cli.group(cls=ValidateMutex(click.Group))
@click.pass_context
@click.option(
    "--controller",
    prompt=True,
    required=True,
    type=click.Choice(["terminal", "chrome"]),
    default="chrome",
    show_envvar=True,
)
@click.option(
    "--navigator",
    prompt=True,
    required=True,
    type=click.Choice(["terminal", "chrome"]),
    default="chrome",
    show_envvar=True,
)
@click.option(
    "--informant",
    prompt=True,
    required=True,
    type=click.Choice(["terminal", "chrome"]),
    default="terminal",
    show_envvar=True,
)
@click.option(
    "--chrome",
    prompt=True,
    type=ChromeChoice(),
    cls=MutexOption,
    not_required_if=["controller=terminal", "navigator=terminal", "informant=terminal"],
    default="launch",
    show_envvar=True,
)
@click.option(
    "--list-validators",
    is_flag=True,
    callback=list_validators,
    expose_value=False,
    is_eager=True,
)
@wrap_docker(exit=False)
def curate(ctx, controller, navigator, informant, chrome=None):
    """
    Runs the interactive curation process in the terminal and/or a Chrome browser.
    
    \b
    You can start a new session using:
    > cmd-iaso curate [...] start [...]
    You can resume aan existing session using:
    > cmd-iaso curate [...] resume [...]
    
    The --controller, --navigator and --informant options define whether each of these
    components will be run in the terminal or inside Chrome. By default, curate uses
    --controller chrome --navigator chrome --informant terminal --chrome launch.
    
    The --chrome option must be provided iff at least one component uses Chrome.
    
    --chrome launch launches a new Chrome browser instance and closes it automatically
    after the curation session has finished.
    
    --chrome IPv4:PORT / --chrome IPv6:PORT / --chrome localhost:PORT connects to a
    running Chrome browser at the specified address. The browser will not automatically
    be closed after the curation session has finished.
    
    \b
    You can launch a new Chrome browser using:
    > chrome --remote-debugging-port=PORT
    
    You can list the registered (not yet validated) validator modules using --list-validators.
    
    \b
    For more information on starting or resuming a curation session, use:
    > cmd-iaso curate start --help
    > cmd-iaso curate resume --help
    """

    pass


@curate.command(cls=ValidateMutex(click.Command))
@click.pass_context
@click.argument(
    "datamine",
    type=click.Path(
        exists=DockerPathExists(), readable=True, dir_okay=False, allow_dash=True
    ),
)
@click.option(
    "--validate",
    "-v",
    "validators",
    multiple=True,
    callback=validate_validators,
    default=["dns-error", "invalid-response", "http-status-error"],
    show_envvar=True,
)
@click.option(
    "--discard-session",
    is_flag=True,
    cls=MutexOption,
    not_required_if=["session"],
    show_envvar=True,
)
@click.option(
    "--session",
    "session_path",
    type=click.Path(exists=False, writable=True, dir_okay=False),
    default="session.gz",
    cls=MutexOption,
    not_required_if=["discard_session"],
    show_envvar=True,
)
@wrap_docker()
@coroutine
async def start(ctx, datamine, validators, discard_session, session_path):
    """
    Starts a new session for the interactive curation process.
    Reads the scraped information on providers from the DATAMINE file path.
    
    -v, --validate VALIDATOR enables the VALIDATOR during the curation session.
    By default the dns-error, invalid-response and http-status-error validators
    will be enabled. If this options is provided at least once, only the validators
    mentioned explicitly in the option will be enabled.
    
    \b
    You can list the registered (not yet validated) validator modules using:
    > cmd-iaso curate --list-validators.
    
    \b
    --session SESSION stores the session information at the SESSION path.
    If this option is not provided, session.gz will be used by default.
    To disable storing the new session altogther, use:
    > cmd-iaso curate [...] start [...] --discard-session [...]
    
    \b
    For more information on the interactive curation process, use:
    > cmd-iaso curate --help
    """

    if session_path is not None and os.path.exists(session_path):
        click.confirm(
            f"{session_path} already exists. Do you want to overwrite {session_path} with a fresh session?",
            abort=True,
        )

    click.echo(
        click.style(f"Loading the datamine file from {datamine} ...", fg="yellow")
    )

    await launch_curation(
        ctx,
        ctx.parent.params["controller"],
        ctx.parent.params["navigator"],
        ctx.parent.params["informant"],
        ctx.parent.params["chrome"],
        CurationSession(session_path, Datamine(datamine), validators, 0, set()),
    )


@curate.command()
@click.pass_context
@click.argument(
    "session",
    type=click.Path(
        exists=DockerPathExists(), readable=True, writable=True, dir_okay=False
    ),
)
@wrap_docker()
@coroutine
async def resume(ctx, session):
    """
    Resumes an existing curation session for the interactive curation process.
    Reads the session information the SESSION file path.
    
    \b
    For more information on the interactive curation process, use:
    > cmd-iaso curate --help
    """

    session_path = session

    click.echo(
        click.style(
            f"Loading the curation session from {session_path} ...", fg="yellow"
        )
    )

    session = CurationSession.load_from_file(
        session_path, partial(validate_validators, ctx, None)
    )

    if len(session.visited) == len(session.datamine.providers):
        click.echo(
            click.style("WARNING: You are working on a completed session.", fg="red")
        )

    await launch_curation(
        ctx,
        ctx.parent.params["controller"],
        ctx.parent.params["navigator"],
        ctx.parent.params["informant"],
        ctx.parent.params["chrome"],
        session,
    )


async def launch_curation(
    ctx, controller, navigator, informant, chrome, session,
):
    async with PyppeteerLauncher(chrome) as launcher:
        Controller = {
            "terminal": TerminalController,
            "chrome": launcher.warp(
                partial(
                    PyppeteerController,
                    url_regex=(None if navigator == "chrome" else r"^.*$"),
                )
            ),
        }[controller]
        Navigator = {
            "terminal": TerminalNavigator,
            "chrome": launcher.warp(PyppeteerNavigator),
        }[navigator]
        Informant = {
            "terminal": TerminalFormatter,
            "chrome": launcher.warp(
                partial(
                    PyppeteerFormatter,
                    url_regex=(None if navigator == "chrome" else r"^.*$"),
                )
            ),
        }[informant]

        await curation.curate(
            ctx_registry(ctx), Controller, Navigator, Informant, session,
        )


@cli.command()
@click.pass_context
@click.option("--port", default=8080, show_envvar=True)
@click.option("--timeout", default=10, show_envvar=True)
@wrap_docker()
def proxy3(ctx, port, timeout):
    """
    Launches a new instance of the HTTPS intercepting data scraping proxy.
    
    --port specifies the port to run the proxy on.
    By default, port 8080 is used.
    
    --timeout specifies the timeout in seconds the proxy will use when
    requesting resources from the Internet.
    By default, a timeout of 10 seconds is used.
    
    As this proxy generates a new self-signed SSL certificate to intercept
    HTTPS requests, you might get security warnings when you use this proxy.
    """
    serve_proxy(port, timeout)


@cli.command(cls=ValidateMutex(click.Command))
@click.pass_context
@click.argument(
    "jobs",
    type=click.Path(exists=False, writable=True, dir_okay=False, allow_dash=True),
)
@click.option(
    "--valid", type=click.IntRange(min=0), default=50, show_envvar=True,
)
@click.option(
    "--random", type=click.IntRange(min=0), default=50, show_envvar=True,
)
@click.option(
    "--valid-namespace-ids",
    prompt=True,
    type=click.Path(
        exists=DockerPathExists(), readable=True, dir_okay=False, allow_dash=True
    ),
    cls=MutexOption,
    not_required_if=["valid=0"],
    show_envvar=True,
)
@wrap_docker()
def jobs(ctx, jobs, valid, random, valid_namespace_ids):
    """
    Generates the jobs for the data scraping subcommand and stores them at the
    JOBS file path.
    
    --valid specifies the number of valid LUIs from VALID_NAMESPACE_IDS to use
    per resource provider.
    By default, the command attempts to include 50 valid LUIs per provider.
    
    --random specifies the number of LUIs that will be generated randomly per
    resource provider from its namespace's LUI regex pattern.
    By default, the command generates 50 random LUIs per provider.
    
    Iff --valid specifies a positive number, --valid-namespace-ids VALID_NAMESPACE_IDS
    must specify the file path to a namespace ids file.
    """

    if os.path.exists(jobs):
        click.confirm(
            f"{jobs} already exists. Do you want to overwrite {jobs} with the new JOBS file?",
            abort=True,
        )

    with click.open_file(jobs, "w") as file:
        json.dump(
            generate_scraping_jobs(
                ctx_registry(ctx),
                valid,
                random,
                NamespaceIds(valid_namespace_ids)
                if valid_namespace_ids is not None
                else None,
            ),
            file,
        )


@cli.command()
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
    "--workers", type=click.IntRange(min=1), default=32, show_envvar=True,
)
@click.option(
    "--timeout", type=click.IntRange(min=5), default=30, show_envvar=True,
)
@wrap_docker()
@coroutine
async def scrape(ctx, jobs, dump, proxy, workers, timeout):
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
        ScrapingJobs(jobs), dump, proxy if proxy != "launch" else None, workers, timeout
    )


@cli.command()
@click.pass_context
@click.argument(
    "dump", type=click.Path(exists=DockerPathExists(), readable=True, file_okay=False)
)
@click.argument(
    "datamine", type=click.Path(exists=False, writable=True, dir_okay=False)
)
@wrap_docker()
def dump2datamine(ctx, dump, datamine):
    """
    Generates the DATAMINE file from the DUMP folder.
    
    \b
    This helper command bridges the gap between the DUMP generated by
    > cmd-iaso scrape [...] DUMP [...]
    and the interactive curation process
    > cmd-iaso curate [...] start DATAMINE [...]
    """

    if os.path.exists(datamine):
        click.confirm(
            f"{datamine} already exists. Do you want to overwrite {datamine} with the new DATAMINE file?",
            abort=True,
        )

    errors = generate_datamine_from_dump(dump, datamine)

    if len(errors) == 0:
        click.echo(
            click.style(
                f"The scraping DUMP at {dump} was successfully converted into a DATAMINE file at {datamine}.",
                fg="green",
            )
        )
    else:
        num_errors = sum(len(errs) for file, errs in errors.items())

        if num_errors == 1:
            click.echo(
                click.style(
                    f"ERROR: There was one erroneous entry in the {list(errors.keys())[0]} file.",
                    fg="red",
                )
            )
        elif len(errors) == 1:
            click.echo(
                click.style(
                    f"ERROR: There were {num_errors} erroneous entries in the {list(errors.keys())[0]} file.",
                    fg="red",
                )
            )
        else:
            click.echo(
                click.style(
                    f"ERROR: There were a total of {num_errors} erroneous entries in the following files:",
                    fg="red",
                )
            )

            for file in errors.keys():
                click.echo(f"- {file}")


def main():
    cli(prog_name="cmd-iaso", auto_envvar_prefix="CMD_IASO")


if __name__ == "__main__":
    main()
