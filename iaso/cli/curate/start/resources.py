import os

import click

from ....click.lazy import lazy_import
from ....click.mutex import ValidateMutex, MutexOption
from ....click.docker import wrap_docker, DockerPathExists
from ....click.coroutine import coroutine

lazy_import(
    globals(),
    """
from ....click.validators import validate_validators

from ....datamine import Datamine

from ....curation.resources import curate_resources
from ....curation.launch import launch_curation
from ....curation.resources_session import ResourcesCurationSession
from ....curation.pyppeteer.resource_navigator import PyppeteerResourceNavigator
""",
)


@click.command(cls=ValidateMutex(click.Command))
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
        ctx.parent.parent.params["statistics"],
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
