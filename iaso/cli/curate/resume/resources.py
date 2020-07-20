from functools import partial

import click

from ....click.lazy import lazy_import
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


@click.command()
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
        ctx.parent.parent.params["statistics"],
        ctx.parent.parent.params["controller"],
        ctx.parent.parent.params["navigator"],
        ctx.parent.parent.params["informant"],
        ctx.parent.parent.params["chrome"],
        ctx.parent.parent.params["tags"],
        ctx.parent.parent.params["ignored_tags"],
        session,
    )
