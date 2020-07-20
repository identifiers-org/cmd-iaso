import os

import click

from ..click.lazy import lazy_import
from ..click.mutex import ValidateMutex, MutexOption
from ..click.docker import wrap_docker, DockerPathExists
from ..click.registry import ensure_registry

lazy_import(
    globals(),
    """
from ..namespace_ids import NamespaceIds
from ..scraping.jobs.generate import generate_scraping_jobs
""",
)


@click.command(cls=ValidateMutex(click.Command))
@click.pass_context
@click.argument(
    "jobs",
    type=click.Path(exists=False, writable=True, dir_okay=False, allow_dash=True),
)
@click.option(
    "--valid", type=click.IntRange(min=0), default=1, show_envvar=True,
)
@click.option(
    "--random", type=click.IntRange(min=0), default=99, show_envvar=True,
)
@click.option(
    "--pings", type=click.IntRange(min=1), default=5, show_envvar=True,
)
@click.option(
    "--valid-namespace-ids",
    prompt=True,
    type=click.Path(exists=DockerPathExists(), readable=True, dir_okay=False),
    cls=MutexOption,
    not_required_if=["valid<2"],
    show_envvar=True,
)
@wrap_docker()
def jobs(ctx, jobs, valid, random, pings, valid_namespace_ids):
    """
    Generates the jobs for the data scraping subcommand and stores them at the
    JOBS file path.
    
    --valid specifies the number of valid LUIs from VALID_NAMESPACE_IDS to use
    per resource provider.
    By default, the command attempts to include 50 valid LUIs per provider.
    
    --random specifies the number of LUIs that will be generated randomly per
    resource provider from its namespace's LUI regex pattern.
    By default, the command generates 50 random LUIs per provider.
    
    --pings specifies the number of times each generated LUI will be pinged
    during the data scraping.
    
    Iff --valid VALID is greater than 1, --valid-namespace-ids VALID_NAMESPACE_IDS
    must specify the file path to a namespace ids file.
    """

    if os.path.exists(jobs):
        click.confirm(
            f"{jobs} already exists. Do you want to overwrite {jobs} with the new JOBS file?",
            abort=True,
        )

    with click.open_file(jobs, "w") as file:
        json.dump(
            generate_scraping_jobs(
                ensure_registry(ctx),
                valid,
                random,
                pings,
                NamespaceIds(valid_namespace_ids)
                if valid_namespace_ids is not None
                else None,
            ),
            file,
        )
