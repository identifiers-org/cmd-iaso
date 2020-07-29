import click

from ..click.docker import wrap_docker
from ..click.lazy import lazy_import

lazy_import(
    globals(),
    """
from ..click.registry import ensure_registry
from ..format_json import format_json
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
