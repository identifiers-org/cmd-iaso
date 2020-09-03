import os

import click
import click_completion
import click_completion.core

from ...click.docker import wrap_docker
from ...click.lazy import LazyCommandGroup

completion_help = """
Shell completion commands for cmd-iaso.
The following shell types are available:

\b
  %s

\b
By default, the current shell is determined automatically.
""" % "\n  ".join(
    "{:<12} {}".format(k, click_completion.core.shells[k])
    for k in sorted(click_completion.core.shells.keys())
)


@click.command(
    cls=LazyCommandGroup("iaso.cli.completion", ["install", "show"]),
    help=completion_help,
)
@click.pass_context
@wrap_docker(exit=False)
def completion(ctx):
    pass
