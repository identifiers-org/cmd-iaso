import os

import click

from ....click.lazy import lazy_import
from ....click.mutex import ValidateMutex, MutexOption
from ....click.docker import wrap_docker, DockerPathExists
from ....click.coroutine import coroutine

lazy_import(
    globals(),
    """
from ....curation.institutions import curate_institutions
from ....curation.institutions_session import InstitutionsCurationSession
from ....curation.launch import launch_curation
from ....curation.pyppeteer.institution_navigator import PyppeteerInstitutionNavigator

from ....institutions.academine import Academine
""",
)


@click.command(cls=ValidateMutex(click.Command))
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
    ctx,
    academine,
    discard_session,
    session,
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
        ctx.parent.parent.params["statistics"],
        ctx.parent.parent.params["controller"],
        ctx.parent.parent.params["navigator"],
        ctx.parent.parent.params["informant"],
        ctx.parent.parent.params["chrome"],
        ctx.parent.parent.params["tags"],
        ctx.parent.parent.params["ignored_tags"],
        InstitutionsCurationSession(
            session,
            Academine(academine),
            0,
            set(),
        ),
    )
