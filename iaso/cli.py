import asyncio

from functools import update_wrapper, partial

import click

from . import curation

from .curation.terminal import (
    TerminalController,
    TerminalNavigator,
    TerminalFormatter,
)
from .curation.pyppeteer import PyppeteerLauncher
from .curation.pyppeteer.controller import PyppeteerController
from .curation.pyppeteer.navigator import PyppeteerNavigator
from .curation.pyppeteer.informant import PyppeteerFormatter

from .click.mutex import ValidateMutexCommand, MutexOption
from .click.chrome import ChromeChoice

from .utils import format_json
from .environment import collect_environment_description
from .registry import Registry
from .datamine import Datamine


def coroutine(f):
    f = asyncio.coroutine(f)

    def wrapper(*args, **kwargs):
        ctx = click.get_current_context()
        ctx.obj["loop"] = asyncio.get_event_loop()
        return ctx.obj["loop"].run_until_complete(f(*args, **kwargs))

    return update_wrapper(wrapper, f)


def ctx_registry(ctx):
    registry = ctx.obj.get("registry")

    if registry is None:
        registry = Registry()
        ctx.obj["registry"] = registry

    return registry


@click.group()
@click.version_option(version="0.0.1")
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)


@cli.command()
@click.pass_context
def environment(ctx):
    """
    Pretty-prints a description of the current environment.
    """
    click.echo(format_json(collect_environment_description()))


@cli.command()
@click.pass_context
def registry(ctx):
    """
    Pretty-prints the current status of the identifiers.org registry.
    """
    click.echo(format_json(ctx_registry(ctx)))


@cli.command(cls=ValidateMutexCommand)
@click.pass_context
@click.argument(
    "datamine", type=click.Path(exists=True, readable=True, allow_dash=True)
)
@click.option(
    "--controller",
    prompt=True,
    required=True,
    type=click.Choice(["terminal", "chrome"]),
    default="chrome",
)
@click.option(
    "--navigator",
    prompt=True,
    required=True,
    type=click.Choice(["terminal", "chrome"]),
    default="chrome",
)
@click.option(
    "--informant",
    prompt=True,
    required=True,
    type=click.Choice(["terminal", "chrome"]),
    default="terminal",
)
@click.option(
    "--chrome",
    prompt=True,
    type=ChromeChoice(),
    cls=MutexOption,
    not_required_if=["controller=terminal", "navigator=terminal", "informant=terminal"],
    default="launch",
)
@click.option("--show-redirect-chain", is_flag=True)
@coroutine
async def curate(
    ctx, datamine, show_redirect_chain, controller, navigator, informant, chrome=None
):
    """
    Runs the interactive curation process in the terminal and/or a Chrome browser.
    Reads the mined information on providers from the DATAMINE JSON file path.
    
    The --chrome option must be provided iff at least one component uses Chrome.
    
    --chrome launch launches a new Chrome browser instance and closes it automatically
    after the curation session has finished.
    
    --chrome IPv4:PORT / --chrome IPv6:PORT connects to a running Chrome browser
    at the specified address. The browser will not automatically be closed after
    the curation session has finished.
    
    \b
    You can launch a new Chrome browser using:
    > chrome --remote-debugging-port=PORT
    """

    async with PyppeteerLauncher(chrome) as launcher:
        Controller = {
            "terminal": TerminalController,
            "chrome": launcher.warp(
                partial(
                    PyppeteerController,
                    url_regex=(None if navigator == "chrome" else r"^.*$"),
                )
            ),
        }[controller]
        Navigator = {
            "terminal": TerminalNavigator,
            "chrome": launcher.warp(PyppeteerNavigator),
        }[navigator]
        Informant = {
            "terminal": TerminalFormatter,
            "chrome": launcher.warp(
                partial(
                    PyppeteerFormatter,
                    url_regex=(None if navigator == "chrome" else r"^.*$"),
                )
            ),
        }[informant]

        await curation.curate(
            ctx_registry(ctx),
            Datamine(datamine),
            Controller,
            Navigator,
            Informant,
            show_redirect_chain,
        )


def main():
    cli(prog_name="cmd-iaso")


if __name__ == "__main__":
    main()
