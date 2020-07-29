import click

from ....click.lazy import LazyCommandGroup
from ....click.docker import wrap_docker


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
