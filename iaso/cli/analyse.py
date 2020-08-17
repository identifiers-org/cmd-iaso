import pickle

import click

from ..click.docker import DockerPathExists, wrap_docker
from ..click.lazy import lazy_import

lazy_import(
    globals(),
    """
from ..analysis import analyse_dumped_information_content
""",
)


def check_athena():
    try:
        import athena
    except ImportError:
        return False

    return True


def check_athena_callback(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    if check_athena():
        click.echo(
            click.style("cmd-iaso has been installed with athena analysis.", fg="green")
        )

        ctx.exit(0)
    else:
        click.echo(
            click.style(
                "cmd-iaso has not been installed with athena analysis.", fg="red"
            )
        )

        ctx.exit(1)


@click.command()
@click.pass_context
@click.argument(
    "dump", type=click.Path(exists=DockerPathExists(), readable=True, file_okay=False)
)
@click.option(
    "--check-athena",
    is_flag=True,
    callback=check_athena_callback,
    expose_value=False,
    is_eager=True,
)
@wrap_docker()
def analyse(ctx, dump):
    """
    Analyses the scraped responses in the DUMP folder to check if
    resource providers are working as expected.

    This command can only be run if cmd-iaso was installed with
    athena analysis. Please make sure you install it with both
    setuptools-rust and Rust installed (see the README for more
    information on the installation process).

    \b
    You can check whether athena analysis is available by running
    > cmd-iaso analyse --check-athena

    This command is still Work In Progress.
    """
    if not check_athena():
        raise click.UsageError(
            click.style(
                "cmd-iaso has not been installed with athena analysis. Please make sure you install it with both setuptools-rust and Rust installed.",
                fg="red",
            )
        )

    analyse_dumped_information_content(dump)
