import pickle

import click

from ..click.lazy import lazy_import
from ..click.docker import wrap_docker

lazy_import(
    globals(),
    """
from tqdm import tqdm
""",
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

    tree = pickle.loads(pickle.dumps(tree))

    click.echo(
        tree.extract_longest_common_non_overlapping_fragments(
            {0}, {1, 2, 3}, debug=False
        )
    )

    click.echo(tree.extract_combination_of_all_common_fragments())

    with tqdm(total=len(tree)) as progress:
        click.echo(
            tree.extract_all_shared_fragments_for_all_strings_parallel(
                progress=progress.update
            )
        )

    with tqdm(total=len(tree)) as progress:
        click.echo(
            tree.extract_all_shared_fragments_for_all_strings_sequential(
                progress=progress.update
            )
        )
