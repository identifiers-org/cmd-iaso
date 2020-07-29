import click

from ....click.lazy import LazyCommandGroup
from ....click.docker import wrap_docker


@click.command(
    cls=LazyCommandGroup("iaso.cli.curate.start", ["resources", "institutions"])
)
@click.pass_context
@wrap_docker(exit=False)
def start(ctx):
    """
    Subcommand to start a new interactive curation process session.
    """
    pass
