import click

from ....click.docker import wrap_docker
from ....click.lazy import LazyCommandGroup


@click.command(
    cls=LazyCommandGroup("iaso.cli.curate.resume", ["resources", "institutions"])
)
@click.pass_context
@wrap_docker(exit=False)
def resume(ctx):
    """
    Subcommand to resume an existing curation session for the interactive curation process.
    """
    pass
