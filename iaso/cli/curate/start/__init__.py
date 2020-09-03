import click

from ....click.docker import wrap_docker
from ....click.lazy import LazyCommandGroup


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
