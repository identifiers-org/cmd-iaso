import click

from ..click.docker import wrap_docker
from ..click.lazy import lazy_import

lazy_import(
    globals(),
    """
from ..environment import collect_environment_description
from ..format_json import format_json
""",
)


@click.command()
@click.pass_context
@wrap_docker()
def environment(ctx):
    """
    Pretty-prints a description of the current environment.
    """
    click.echo(format_json(collect_environment_description()))
