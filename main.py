import click

from iaso import curation

from iaso.utils import echo_json
from iaso.environment import collect_environment_description
from iaso.registry import Registry
from iaso.datamine import Datamine

import asyncio
from functools import update_wrapper


def coroutine(f):
    f = asyncio.coroutine(f)

    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))

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
    echo_json(collect_environment_description())


@cli.command()
@click.pass_context
def registry(ctx):
    """
    Pretty-prints the current status of the identifiers.org registry.
    """
    echo_json(ctx_registry(ctx))


@cli.group()
@click.pass_context
@click.argument("datamine", type=click.Path(exists=True, readable=True))
def curate(ctx, datamine):
    """
    Runs the interactive curation process in the terminal or a Chrome browser.
    Reads the mined information on providers from the DATAMINE JSON file path.
    """
    ctx.obj["datamine"] = Datamine(datamine)


@curate.command()
@click.pass_context
@coroutine
async def terminal(ctx):
    """
    Runs the interactive curation process in the terminal.
    """
    await curation.curate(
        ctx_registry(ctx),
        ctx.obj["datamine"],
        curation.TerminalController,
        curation.TerminalFormatter,
    )


@curate.command()
@click.pass_context
@coroutine
async def launch(ctx):
    """
    Runs the interactive curation process in a Chrome browser.
    Launches a new Chrome browser instances.
    The browser will automatically be closed once the curation session finished.
    """
    await curation.curate(
        ctx_registry(ctx),
        ctx.obj["datamine"],
        curation.PyppeteerController.Launch,
        curation.PyppeteerFormatter,
    )


@curate.command()
@click.pass_context
@click.argument("address")
@coroutine
async def connect(ctx, address):
    """
    Runs the interactive curation process in a Chrome browser.
    Connects to a running Chrome browser instance at ADDRESS.
    The browser will not automatically be closed once the curation session finished.
    ADDRESS is an IPv4 'IP:PORT' or IPv6 '[IP]:PORT' address.
    You can launch a new Chrome browser using\n
     > chrome --remote-debugging-port=PORT
    """
    await curation.curate(
        ctx_registry(ctx),
        ctx.obj["datamine"],
        curation.PyppeteerController.Connect(address),
        curation.PyppeteerFormatter,
    )


if __name__ == "__main__":
    cli(prog_name="cmd-iaso")

# TODO: reorganise such that you can combine three components freely
# - URL viewer (terminal vs go to in browser)
# - navigation (terminal prompt vs browser buttons)
# - information (terminal vs info button + overlay)
