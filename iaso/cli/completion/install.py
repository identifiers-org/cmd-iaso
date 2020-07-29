import click_completion
import click
import click_completion.core

from ...click.docker import wrap_docker


@click.command()
@click.pass_context
@click.option(
    "--append/--overwrite", help="Append the completion code to the file", default=None
)
@click.option(
    "-i", "--case-insensitive/--no-case-insensitive", help="Case insensitive completion"
)
@click.argument(
    "shell",
    required=False,
    type=click_completion.DocumentedChoice(click_completion.core.shells),
)
@click.argument(
    "path", required=False, type=click.Path(exists=False, writable=True, dir_okay=False)
)
@wrap_docker()
def install(ctx, append, case_insensitive, shell, path):
    """
    Installs shell completion for cmd-iaso in the selected SHELL at PATH.

    \b
    --append appends the completion code to the file at PATH.
    --overwrite overwrites the file at PATH with just the completion code.

    -i enables case insensitive completion.
    """
    extra_env = (
        {"_CMD_IASO_CASE_INSENSITIVE_COMPLETE": "ON"} if case_insensitive else {}
    )
    shell, path = click_completion.core.install(
        shell=shell, path=path, append=append, extra_env=extra_env
    )
    click.echo("%s completion installed in %s" % (shell, path))
