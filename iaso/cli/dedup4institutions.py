import os

import click

from ..click.lazy import lazy_import
from ..click.docker import wrap_docker
from ..click.coroutine import coroutine
from ..click.registry import ensure_registry

lazy_import(
    globals(),
    """
from ..institutions import deduplicate_registry_institutions
""",
)


@click.command()
@click.pass_context
@click.argument(
    "academine", type=click.Path(exists=False, writable=True, dir_okay=False)
)
@wrap_docker()
@coroutine
async def dedup4institutions(ctx, academine):
    """
    Collects all existing institutions from the registry and attempts to link them to their real entities to
    deduplicate the entries and disentangle concatenations of institution names.
    
    The command also tries to fill in information about the institutions like their name, official URL,
    ROR ID, country and a description.
    
    The results of this command are stored in the ACADEMINE file.
    """

    if os.path.exists(academine):
        click.confirm(
            f"{academine} already exists. Do you want to overwrite {academine} with the new ACADEMINE file?",
            abort=True,
        )

    await deduplicate_registry_institutions(ensure_registry(ctx), academine)
