import asyncio
import json
import os
import re
import socket
from functools import partial, update_wrapper
from pathlib import Path

import click
import click_completion
import click_completion.core
from dotenv import load_dotenv

from .cli2.test import environment
from .cli2.test2 import test2
from .click.chrome import ChromeChoice
from .click.docker import (
    DockerPathExists,
    docker_chrome_path,
    register_docker,
    wrap_docker,
)
from .click.mutex import MutexOption, ValidateMutex

load_dotenv(dotenv_path=(Path(".") / ".env"))


def completion_startswith(string, incomplete):
    """A custom completion matching that supports case insensitive matching"""
    if os.environ.get("_CMD_IASO_CASE_INSENSITIVE_COMPLETE"):
        string = string.lower()
        incomplete = incomplete.lower()
    return string.startswith(incomplete)


click_completion.core.startswith = completion_startswith
click_completion.init()


IMPORT_PATTERN = re.compile(
    r"from\s+(\.?(?:[a-zA-Z_][a-zA-Z0-9_]*)?(?:\.(?:[a-zA-Z_][a-zA-Z0-9_]*))*)\s+import\s+(?:\(\s*)?((?:(?:[a-zA-Z_][a-zA-Z0-9_]*)(?:\s+as\s+[a-zA-Z_][a-zA-Z0-9_]*)?(?:,\s*)?)+)\s*\)?"
)


def lazy_import(imports):
    import importlib

    def LazyImportWrapper(path, name, glob):
        class LazyImport:
            def __getattribute__(self, attr):
                module = importlib.import_module(path, package="iaso")
                helper = getattr(module, name)

                globals()[glob] = helper

                return getattr(helper, attr)

            def __call__(self, *args, **kwargs):
                module = importlib.import_module(path, package="iaso")
                helper = getattr(module, name)

                globals()[glob] = helper

                return helper(*args, **kwargs)

        return LazyImport()

    globs = globals()

    for match in IMPORT_PATTERN.finditer(imports):
        import_path = match.group(1)

        imports = match.group(2).split(",")

        for r_import in imports:
            r_import = r_import.strip()

            if len(r_import) == 0:
                continue

            import_split = re.split(r"\sas\s", r_import)

            import_name = import_split[0].strip()
            import_as = import_split[len(import_split) - 1].strip()

            globs[import_as] = LazyImportWrapper(import_path, import_name, import_as)


lazy_import(
    """
from .curation.resources import curate_resources
from .curation.institutions import curate_institutions

from .curation.resources_session import ResourcesCurationSession
from .curation.institutions_session import InstitutionsCurationSession

from .curation.tag_store import TagStore

from .curation.terminal.controller import TerminalController
from .curation.terminal.navigator import TerminalNavigator
from .curation.terminal.informant import TerminalInformant

from .curation.pyppeteer import PyppeteerLauncher
from .curation.pyppeteer.controller import PyppeteerController
from .curation.pyppeteer.resource_navigator import PyppeteerResourceNavigator
from .curation.pyppeteer.institution_navigator import PyppeteerInstitutionNavigator
from .curation.pyppeteer.informant import PyppeteerInformant

from .click.validators import (
    validate_validators,
    list_validators,
)

from .scraping.http.proxy3 import serve as serve_proxy
from .scraping import scrape_resources

from .dump2datamine import generate_datamine_from_dump

from .valid_luis import validate_resolution_endpoint, collect_namespace_ids_from_logs

from .format_json import format_json
from .environment import collect_environment_description
from .registry import Registry
from .datamine import Datamine
from .namespace_ids import NamespaceIds
from .scraping.jobs import ScrapingJobs
from .scraping.jobs.generate import generate_scraping_jobs

from .institutions import deduplicate_registry_institutions
from .institutions.academine import Academine
"""
)


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
        click.echo(click.style("Loading the identifiers.org registry ...", fg="yellow"))

        registry = Registry()
        ctx.obj["registry"] = registry

    return registry


def get_version():
    try:
        from importlib import metadata

        return metadata.version("cmd-iaso")
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


install_help = """
Shell completion commands for cmd-iaso.
The following shell types are available:

\b
  %s

\b
By default, the current shell is determined automatically.
""" % "\n  ".join(
    "{:<12} {}".format(k, click_completion.core.shells[k])
    for k in sorted(click_completion.core.shells.keys())
)


@cli.group(help=install_help)
@click.pass_context
@wrap_docker(exit=False)
def completion(ctx):
    pass


@completion.command()
@click.pass_context
@click.option(
    "-i", "--case-insensitive/--no-case-insensitive", help="Case insensitive completion"
)
@click.argument(
    "shell",
    required=False,
    type=click_completion.DocumentedChoice(click_completion.core.shells),
)
@wrap_docker()
def show(ctx, shell, case_insensitive):
    """
    Shows the code to enable shell completion for cmd-iaso in the selected shell.

    -i enables case insensitive completion.
    """
    extra_env = (
        {"_CMD_IASO_CASE_INSENSITIVE_COMPLETE": "ON"} if case_insensitive else {}
    )
    click.echo(click_completion.core.get_code(shell, extra_env=extra_env))


@completion.command()
@click.pass_context
@click.option(
    "--append/--overwrite", help="Append the completion code to the file", default=None
)
@click.option(
    "-i", "--case-insensitive/--no-case-insensitive", help="Case insensitive completion"
)
@click.argument(
    "shell",
    required=False,
    type=click_completion.DocumentedChoice(click_completion.core.shells),
)
@click.argument(
    "path", required=False, type=click.Path(exists=False, writable=True, dir_okay=False)
)
@wrap_docker()
def install(ctx, append, case_insensitive, shell, path):
    """
    Installs shell completion for cmd-iaso in the selected SHELL at PATH.

    \b
    --append appends the completion code to the file at PATH.
    --overwrite overwrites the file at PATH with just the completion code.

    -i enables case insensitive completion.
    """
    extra_env = (
        {"_CMD_IASO_CASE_INSENSITIVE_COMPLETE": "ON"} if case_insensitive else {}
    )
    shell, path = click_completion.core.install(
        shell=shell, path=path, append=append, extra_env=extra_env
    )
    click.echo("%s completion installed in %s" % (shell, path))


# @cli.command()
# @click.pass_context
# @wrap_docker()
# def environment(ctx):
#    """
#    Pretty-prints a description of the current environment.
#    """
#    click.echo(format_json(collect_environment_description()))


cli.add_command(environment)


cli.add_command(test2)


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
    "--tags",
    type=click.Path(exists=False, writable=True, dir_okay=False),
    default="tags.gz",
    show_envvar=True,
)
@click.option(
    "--ignore",
    "-i",
    "ignored_tags",
    multiple=True,
    default=["fixed", "ignore"],
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
def curate(ctx, controller, navigator, informant, tags, ignored_tags, chrome=None):
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

    --tags TAGS changes the path where the cross-session tags will be stored.
    By default, tags.gz will be used.

    --ignore TAG / -i TAG can be used to explicitly set the tags which will be
    ignored during the this run of cmd-iaso (more specifically, any suggested curation
    entry with this tag will not be shown). Note that this selection can be changed
    at any time while the interactive curation process is running.
    By default, 'fixed' and 'ignore' will be ignored.
    
    You can list the registered (not yet validated) validator modules using --list-validators.
    
    \b
    For more information on starting or resuming a curation session, use:
    > cmd-iaso curate start --help
    > cmd-iaso curate resume --help
    """

    pass


@curate.group()
@click.pass_context
@wrap_docker(exit=False)
def start(ctx):
    """
    Subcommand to start a new interactive curation process session.
    """
    pass


@start.command(cls=ValidateMutex(click.Command))
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
    "--valid-luis-threshold", type=click.IntRange(0, 100), default=0, show_envvar=True,
)
@click.option(
    "--random-luis-threshold",
    type=click.IntRange(0, 100),
    default=100,
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
    type=click.Path(exists=False, writable=True, dir_okay=False),
    default="resources_session.gz",
    cls=MutexOption,
    not_required_if=["discard_session"],
    show_envvar=True,
)
@wrap_docker()
@coroutine
async def resources(
    ctx,
    datamine,
    validators,
    valid_luis_threshold,
    random_luis_threshold,
    discard_session,
    session,
):
    """
    Starts a new session for the interactive curation process of resource providers.
    Reads the scraped information on providers from the DATAMINE file path.
    
    -v, --validate VALIDATOR enables the VALIDATOR during the curation session.
    By default the dns-error, invalid-response and http-status-error validators
    will be enabled. If this options is provided at least once, only the validators
    mentioned explicitly in the option will be enabled.
    
    \b
    You can list the registered (not yet validated) validator modules using:
    > cmd-iaso curate --list-validators.
    
    --valid-luis-threshold specifies the percentage of pings with valid LUIs to a
    resource which must exhibit an error for it to be reported.
    By default, all errors to valid LUIs are reported.
    Each validator can choose whether to abide by this option or not.
    
    --random-luis-threshold specifies the percentage of pings with random LUIS to
    a resource which must exhibit an error for it to be reported.
    By default, no errors to random LUIs are reported.
    Each validator can choose whether to abide by this option or not.
    
    \b
    --session SESSION stores the session information at the SESSION path.
    If this option is not provided, resources_session.gz will be used by default.
    To disable storing the new session altogther, use:
    > cmd-iaso curate [...] start resources [...] --discard-session [...]
    
    \b
    For more information on the interactive curation process, use:
    > cmd-iaso curate --help
    """

    if session is not None and os.path.exists(session):
        click.confirm(
            f"{session} already exists. Do you want to overwrite {session} with a fresh session?",
            abort=True,
        )

    click.echo(
        click.style(f"Loading the datamine file from {datamine} ...", fg="yellow")
    )

    await launch_curation(
        curate_resources,
        PyppeteerResourceNavigator,
        ctx,
        ctx.parent.parent.params["controller"],
        ctx.parent.parent.params["navigator"],
        ctx.parent.parent.params["informant"],
        ctx.parent.parent.params["chrome"],
        ctx.parent.parent.params["tags"],
        ctx.parent.parent.params["ignored_tags"],
        ResourcesCurationSession(
            session,
            Datamine(datamine),
            validators,
            valid_luis_threshold,
            random_luis_threshold,
            0,
            set(),
        ),
    )


@start.command(cls=ValidateMutex(click.Command))
@click.pass_context
@click.argument(
    "academine",
    type=click.Path(
        exists=DockerPathExists(), readable=True, dir_okay=False, allow_dash=True
    ),
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
    type=click.Path(exists=False, writable=True, dir_okay=False),
    default="institutions_session.gz",
    cls=MutexOption,
    not_required_if=["discard_session"],
    show_envvar=True,
)
@wrap_docker()
@coroutine
async def institutions(
    ctx, academine, discard_session, session,
):
    """
    Starts a new session for the interactive curation process of institutions.
    Reads the deduplicated information on institutions from the ACADEMINE file path.
    
    \b
    --session SESSION stores the session information at the SESSION path.
    If this option is not provided, institutions_session.gz will be used by default.
    To disable storing the new session altogther, use:
    > cmd-iaso curate [...] start institutions [...] --discard-session [...]
    
    \b
    For more information on the interactive curation process, use:
    > cmd-iaso curate --help
    """

    if session is not None and os.path.exists(session):
        click.confirm(
            f"{session} already exists. Do you want to overwrite {session} with a fresh session?",
            abort=True,
        )

    click.echo(
        click.style(f"Loading the academine file from {academine} ...", fg="yellow")
    )

    await launch_curation(
        curate_institutions,
        PyppeteerInstitutionNavigator,
        ctx,
        ctx.parent.parent.params["controller"],
        ctx.parent.parent.params["navigator"],
        ctx.parent.parent.params["informant"],
        ctx.parent.parent.params["chrome"],
        ctx.parent.parent.params["tags"],
        ctx.parent.parent.params["ignored_tags"],
        InstitutionsCurationSession(session, Academine(academine), 0, set(),),
    )


@curate.group()
@click.pass_context
@wrap_docker(exit=False)
def resume(ctx):
    """
    Subcommand to resume an existing curation session for the interactive curation process.
    """
    pass


@resume.command()
@click.pass_context
@click.argument(
    "session",
    type=click.Path(
        exists=DockerPathExists(), readable=True, writable=True, dir_okay=False
    ),
)
@wrap_docker()
@coroutine
async def resources(ctx, session):
    """
    Resumes an existing curation session for the interactive curation process
    of resource providers.
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

    session = ResourcesCurationSession.load_from_file(
        session_path, partial(validate_validators, ctx, None)
    )

    if len(session.visited) == len(session):
        click.echo(
            click.style("WARNING: You are working on a completed session.", fg="red")
        )

    await launch_curation(
        curate_resources,
        PyppeteerResourceNavigator,
        ctx,
        ctx.parent.parent.params["controller"],
        ctx.parent.parent.params["navigator"],
        ctx.parent.parent.params["informant"],
        ctx.parent.parent.params["chrome"],
        ctx.parent.parent.params["tags"],
        ctx.parent.parent.params["ignored_tags"],
        session,
    )


@resume.command()
@click.pass_context
@click.argument(
    "session",
    type=click.Path(
        exists=DockerPathExists(), readable=True, writable=True, dir_okay=False
    ),
)
@wrap_docker()
@coroutine
async def institutions(ctx, session):
    """
    Resumes an existing curation session for the interactive curation process
    of institutions.
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

    session = InstitutionsCurationSession.load_from_file(session_path)

    if len(session.visited) == len(session):
        click.echo(
            click.style("WARNING: You are working on a completed session.", fg="red")
        )

    await launch_curation(
        curate_institutions,
        PyppeteerInstitutionNavigator,
        ctx,
        ctx.parent.parent.params["controller"],
        ctx.parent.parent.params["navigator"],
        ctx.parent.parent.params["informant"],
        ctx.parent.parent.params["chrome"],
        ctx.parent.parent.params["tags"],
        ctx.parent.parent.params["ignored_tags"],
        session,
    )


async def launch_curation(
    curation_func,
    ChromeNavigator,
    ctx,
    controller,
    navigator,
    informant,
    chrome,
    tags,
    ignored_tags,
    session,
):
    if not os.path.exists(tags):
        click.confirm(
            f"{tags} does not exist yet. Do you want to start with a new cross-session tags store?",
            abort=True,
        )

        tag_store = TagStore(tags)
    else:
        tag_store = TagStore.load_from_file(tags)

    async with PyppeteerLauncher(chrome) as launcher:
        Controller = {
            "terminal": partial(
                TerminalController, control_tags=(informant != "chrome")
            ),
            "chrome": launcher.warp(
                partial(
                    PyppeteerController,
                    url_regex=(None if navigator == "chrome" else r"^.*$"),
                )
            ),
        }[controller]
        Navigator = {
            "terminal": TerminalNavigator,
            "chrome": launcher.warp(ChromeNavigator),
        }[navigator]
        Informant = {
            "terminal": partial(
                TerminalInformant,
                ignored_tags,
                control_tags=(controller != "terminal"),
            ),
            "chrome": launcher.warp(
                partial(
                    PyppeteerInformant,
                    ignored_tags,
                    url_regex=(None if navigator == "chrome" else r"^.*$"),
                )
            ),
        }[informant]

        await curation_func(
            ctx_registry(ctx), Controller, Navigator, Informant, tag_store, session,
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


@cli.command()
@click.pass_context
@click.argument(
    "logs", type=click.Path(exists=DockerPathExists(), readable=True, file_okay=False),
)
@click.argument(
    "valid-namespace-ids", type=click.Path(exists=False, writable=True, dir_okay=False),
)
@click.option(
    "--resolution-endpoint",
    default="https://resolver.api.identifiers.org/",
    prompt=True,
    show_envvar=True,
)
def logs2luis(ctx, logs, valid_namespace_ids, resolution_endpoint):
    """
    Extracts valid LUIs from the load balancing LOGS folder of identifiers.org
    and saves them to the VALID_NAMESPACE_IDS file.
    
    \b
    This helper command can be used to generate VALID_NAMESPACE_IDS file required
    to run:
    > cmd-iaso jobs --valid VALID
    with VALID > 1 to include LUIs from the logs
    
    --resolution-endpoint specifies the resolution API endpoint of identifiers.org.
    This option can be used to run a local deployment of the identifiers.org
    resolution service instead of relying on the public one.
    """

    if os.path.exists(valid_namespace_ids):
        click.confirm(
            f"{valid_namespace_ids} already exists. Do you want to overwrite {valid_namespace_ids} with the newly extracted valid namespace ids?",
            abort=True,
        )

    validate_resolution_endpoint(resolution_endpoint)

    collect_namespace_ids_from_logs(logs, resolution_endpoint, valid_namespace_ids)


@cli.command(cls=ValidateMutex(click.Command))
@click.pass_context
@click.argument(
    "jobs",
    type=click.Path(exists=False, writable=True, dir_okay=False, allow_dash=True),
)
@click.option(
    "--valid", type=click.IntRange(min=0), default=1, show_envvar=True,
)
@click.option(
    "--random", type=click.IntRange(min=0), default=99, show_envvar=True,
)
@click.option(
    "--pings", type=click.IntRange(min=1), default=5, show_envvar=True,
)
@click.option(
    "--valid-namespace-ids",
    prompt=True,
    type=click.Path(exists=DockerPathExists(), readable=True, dir_okay=False),
    cls=MutexOption,
    not_required_if=["valid<2"],
    show_envvar=True,
)
@wrap_docker()
def jobs(ctx, jobs, valid, random, pings, valid_namespace_ids):
    """
    Generates the jobs for the data scraping subcommand and stores them at the
    JOBS file path.
    
    --valid specifies the number of valid LUIs from VALID_NAMESPACE_IDS to use
    per resource provider.
    By default, the command attempts to include 50 valid LUIs per provider.
    
    --random specifies the number of LUIs that will be generated randomly per
    resource provider from its namespace's LUI regex pattern.
    By default, the command generates 50 random LUIs per provider.
    
    --pings specifies the number of times each generated LUI will be pinged
    during the data scraping.
    
    Iff --valid VALID is greater than 1, --valid-namespace-ids VALID_NAMESPACE_IDS
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
                pings,
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


@cli.command()
@click.pass_context
@click.argument(
    "academine", type=click.Path(exists=False, writable=True, dir_okay=False)
)
@wrap_docker()
@coroutine
async def dedup4institutions(ctx, academine):
    """
    Collects all existing institutions from the registry and attempts to link them to their real entities to
    deduplicate the entries and disentangle concatenations of institution names.
    
    The command also tries to fill in information about the institutions like their name, official URL,
    ROR ID, country and a description.
    
    The results of this command are stored in the ACADEMINE file.
    """

    if os.path.exists(academine):
        click.confirm(
            f"{academine} already exists. Do you want to overwrite {academine} with the new ACADEMINE file?",
            abort=True,
        )

    await deduplicate_registry_institutions(ctx_registry(ctx), academine)


def main():
    cli(prog_name="cmd-iaso", auto_envvar_prefix="CMD_IASO")


if __name__ == "__main__":
    main()
