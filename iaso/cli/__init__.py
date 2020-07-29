import os

from pathlib import Path

import click
import click_completion
import click_completion.core

from dotenv import load_dotenv

from ..click.docker import register_docker
from ..click.lazy import LazyCommandGroup

load_dotenv(dotenv_path=(Path(".") / ".env"))


def completion_startswith(string, incomplete):
    """A custom completion matching that supports case insensitive matching"""
    if os.environ.get("_CMD_IASO_CASE_INSENSITIVE_COMPLETE"):
        string = string.lower()
        incomplete = incomplete.lower()
    return string.startswith(incomplete)


click_completion.core.startswith = completion_startswith
click_completion.init()


def get_version():
    try:
        from importlib import metadata

        return metadata.version("cmd-iaso")
    except ImportError:
        # Running on pre-3.8 Python
        import pkg_resources

        return pkg_resources.get_distribution("cmd-iaso").version


@click.command(
    cls=LazyCommandGroup(
        "iaso.cli",
        [
            "completion",
            "environment",
            "registry",
            "logs2luis",
            "jobs",
            "proxy3",
            "scrape",
            "dump2datamine",
            "dedup4institutions",
            "curate",
        ],
    )
)
@click.version_option(version=get_version())
@click.pass_context
@click.option(
    "--docker",
    type=click.Path(exists=False),
    hidden=True,
    allow_from_autoenv=False,
    is_eager=True,
    callback=register_docker,
    expose_value=False,
)
def cli(ctx):
    ctx.ensure_object(dict)


def main():
    cli(prog_name="cmd-iaso", auto_envvar_prefix="CMD_IASO")


if __name__ == "__main__":
    main()
