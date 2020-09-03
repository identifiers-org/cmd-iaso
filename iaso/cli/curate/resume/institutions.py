import click

from ....click.coroutine import coroutine
from ....click.docker import DockerPathExists, wrap_docker
from ....click.lazy import lazy_import

lazy_import(
    globals(),
    """
from ....curation.institutions import curate_institutions
from ....curation.institutions_session import InstitutionsCurationSession
from ....curation.launch import launch_curation
from ....curation.pyppeteer.institution_navigator import PyppeteerInstitutionNavigator
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
        ctx.parent.parent.params["statistics"],
        ctx.parent.parent.params["controller"],
        ctx.parent.parent.params["navigator"],
        ctx.parent.parent.params["informant"],
        ctx.parent.parent.params["chrome"],
        ctx.parent.parent.params["tags"],
        ctx.parent.parent.params["ignored_tags"],
        session,
    )
