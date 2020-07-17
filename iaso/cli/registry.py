import click

from ..click.lazy import lazy_import
from ..click.docker import wrap_docker

lazy_import(
    globals(),
    """
from ..format_json import format_json
from ..click.registry import ensure_registry
""",
)


@click.command()
@click.pass_context
@wrap_docker()
def registry(ctx):
    """
    Pretty-prints the current status of the identifiers.org registry.
    """
    click.echo(format_json(ensure_registry(ctx)))
