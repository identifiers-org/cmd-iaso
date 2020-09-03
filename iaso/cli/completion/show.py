import click
import click_completion
import click_completion.core

from ...click.docker import wrap_docker


@click.command()
@click.pass_context
@click.option(
    "-i", "--case-insensitive/--no-case-insensitive", help="Case insensitive completion"
)
@click.argument(
    "shell",
    required=False,
    type=click_completion.DocumentedChoice(click_completion.core.shells),
)
@wrap_docker()
def show(ctx, shell, case_insensitive):
    """
    Shows the code to enable shell completion for cmd-iaso in the selected shell.

    -i enables case insensitive completion.
    """
    extra_env = (
        {"_CMD_IASO_CASE_INSENSITIVE_COMPLETE": "ON"} if case_insensitive else {}
    )
    click.echo(click_completion.core.get_code(shell, extra_env=extra_env))
