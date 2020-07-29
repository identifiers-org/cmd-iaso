import click

from ..registry import Registry


def ensure_registry(ctx):
    registry = ctx.obj.get("registry")

    if registry is None:
        click.echo(click.style("Loading the identifiers.org registry ...", fg="yellow"))

        registry = Registry()
        ctx.obj["registry"] = registry

    return registry
