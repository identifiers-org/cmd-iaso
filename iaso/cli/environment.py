import click

from ..click.lazy import lazy_import
from ..click.docker import wrap_docker

lazy_import(
    globals(),
    """
from ..format_json import format_json
from ..environment import collect_environment_description
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
