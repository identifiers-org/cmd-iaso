import os

import click

from ..click.docker import DockerPathExists, wrap_docker
from ..click.lazy import lazy_import

lazy_import(
    globals(),
    """
from ..dump2datamine import generate_datamine_from_dump
""",
)


@click.command()
@click.pass_context
@click.argument(
    "dump", type=click.Path(exists=DockerPathExists(), readable=True, file_okay=False)
)
@click.argument(
    "datamine", type=click.Path(exists=False, writable=True, dir_okay=False)
)
@wrap_docker()
def dump2datamine(ctx, dump, datamine):
    """
    Generates the DATAMINE file from the DUMP folder.

    \b
    This helper command bridges the gap between the DUMP generated by
    > cmd-iaso scrape [...] DUMP [...]
    and the interactive curation process
    > cmd-iaso curate [...] start DATAMINE [...]
    """

    if os.path.exists(datamine):
        click.confirm(
            f"{datamine} already exists. Do you want to overwrite {datamine} with the new DATAMINE file?",
            abort=True,
        )

    errors = generate_datamine_from_dump(dump, datamine)

    if len(errors) == 0:
        click.echo(
            click.style(
                f"The scraping DUMP at {dump} was successfully converted into a DATAMINE file at {datamine}.",
                fg="green",
            )
        )
    else:
        num_errors = sum(len(errs) for file, errs in errors.items())

        if num_errors == 1:
            click.echo(
                click.style(
                    f"ERROR: There was one erroneous entry in the {list(errors.keys())[0]} file.",
                    fg="red",
                )
            )
        elif len(errors) == 1:
            click.echo(
                click.style(
                    f"ERROR: There were {num_errors} erroneous entries in the {list(errors.keys())[0]} file.",
                    fg="red",
                )
            )
        else:
            click.echo(
                click.style(
                    f"ERROR: There were a total of {num_errors} erroneous entries in the following files:",
                    fg="red",
                )
            )

            for file in errors.keys():
                click.echo(f"- {file}")
