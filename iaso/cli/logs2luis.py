import os

import click

from ..click.lazy import lazy_import
from ..click.docker import wrap_docker, DockerPathExists

lazy_import(
    globals(),
    """
from ..valid_luis import validate_resolution_endpoint, collect_namespace_ids_from_logs
""",
)


@click.command()
@click.pass_context
@click.argument(
    "logs", type=click.Path(exists=DockerPathExists(), readable=True, file_okay=False),
)
@click.argument(
    "valid-namespace-ids", type=click.Path(exists=False, writable=True, dir_okay=False),
)
@click.option(
    "--resolution-endpoint",
    default="https://resolver.api.identifiers.org/",
    prompt=True,
    show_envvar=True,
)
def logs2luis(ctx, logs, valid_namespace_ids, resolution_endpoint):
    """
    Extracts valid LUIs from the load balancing LOGS folder of identifiers.org
    and saves them to the VALID_NAMESPACE_IDS file.
    
    \b
    This helper command can be used to generate VALID_NAMESPACE_IDS file required
    to run:
    > cmd-iaso jobs --valid VALID
    with VALID > 1 to include LUIs from the logs
    
    --resolution-endpoint specifies the resolution API endpoint of identifiers.org.
    This option can be used to run a local deployment of the identifiers.org
    resolution service instead of relying on the public one.
    """

    if os.path.exists(valid_namespace_ids):
        click.confirm(
            f"{valid_namespace_ids} already exists. Do you want to overwrite {valid_namespace_ids} with the newly extracted valid namespace ids?",
            abort=True,
        )

    validate_resolution_endpoint(resolution_endpoint)

    collect_namespace_ids_from_logs(logs, resolution_endpoint, valid_namespace_ids)
