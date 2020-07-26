import click

from ..click.lazy import lazy_import
from ..click.docker import wrap_docker

lazy_import(
    globals(), """""",
)


@click.command()
@click.pass_context
@wrap_docker()
def analyse(ctx):
    """
    WIP: Will be the command to analyse the data dump
    """
    try:
        from athena import SharedFragmentTree
    except ImportError:
        raise click.UsageError(
            click.style(
                "cmd-iaso has not been installed with athena analysis. Please make sure you install it with both setuptools-rust and Rust installed.",
                fg="red",
            )
        )

    strings = [("a", "b", "c", "d", "e"), ("a", "b", "c"), ("c", "d", "e"), ("b", "c")]

    tree = SharedFragmentTree(strings)

    click.echo(
        tree.extract_longest_common_non_overlapping_substrings(
            {0}, {1, 2, 3}, debug=True
        )
    )
