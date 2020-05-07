import click

from iaso import curation
from iaso.curation.terminal import (
    TerminalController,
    TerminalNavigator,
    TerminalFormatter,
)
from iaso.curation.pyppeteer import (
    PyppeteerLauncher,
    PyppeteerController,
    PyppeteerNavigator,
    PyppeteerFormatter,
)

from iaso.utils import format_json
from iaso.environment import collect_environment_description
from iaso.registry import Registry
from iaso.datamine import Datamine

import asyncio
import ipaddress
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
    click.echo(format_json(collect_environment_description()))


@cli.command()
@click.pass_context
def registry(ctx):
    """
    Pretty-prints the current status of the identifiers.org registry.
    """
    click.echo(format_json(ctx_registry(ctx)))


# @cli.group()
# @click.pass_context
# @click.argument("datamine", type=click.Path(exists=True, readable=True))
# def curate(ctx, datamine):
#    """
#    Runs the interactive curation process in the terminal or a Chrome browser.
#    Reads the mined information on providers from the DATAMINE JSON file path.
#    """
#    ctx.obj["datamine"] = Datamine(datamine)


class Mutex(click.Option):
    def __init__(self, *args, **kwargs):
        self.not_required_if = kwargs.pop("not_required_if")

        assert self.not_required_if is not None, "'not_required_if' parameter required"

        kwargs["help"] = (
            kwargs.get("help", "")
            + "Option is mutually exclusive with "
            + ", ".join(self.not_required_if)
            + "."
        ).strip()

        super(Mutex, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        exlusivity = []

        for mutex_opt in self.not_required_if:
            mutex_opt_name, mutext_opt_val = mutex_opt.split("=")

            if "=" in mutex_opt:
                exlusivity.append(f"--{mutex_opt_name} {mutext_opt_val}")
            else:
                exlusivity.append(f"--{mutex_opt_name}")

            if (mutex_opt_name not in ctx.params) or (
                ("=" in mutex_opt) and (ctx.params[mutex_opt_name] != mutext_opt_val)
            ):
                return super(Mutex, self).handle_parse_result(ctx, opts, args)

        if self.name in opts:
            raise click.UsageError(
                "illegal usage: '{name}' is mutually exclusive with '{exclusivity}'.".format(
                    name=self.name, exclusivity=" ".join(exlusivity)
                )
            )

        self.prompt = None
        self.default = None

        return super(Mutex, self).handle_parse_result(ctx, opts, args)


class ChromeChoice(click.Choice):
    name = "chrome-choice"

    def __init__(self, case_sensitive=True):
        self.choices = ["'launch'", "IPv4:PORT", "[IPv6]:PORT"]
        self.case_sensitive = case_sensitive

    def convert(self, value, param, ctx):
        normed_value = value
        normed_choices = {"launch": "launch"}

        if ctx is not None and ctx.token_normalize_func is not None:
            normed_value = ctx.token_normalize_func(value)
            normed_choices = {
                ctx.token_normalize_func(normed_choice): original
                for normed_choice, original in normed_choices.items()
            }

        if not self.case_sensitive:
            normed_value = normed_value.casefold()
            normed_choices = {
                normed_choice.casefold(): original
                for normed_choice, original in normed_choices.items()
            }

        if normed_value in normed_choices:
            return normed_choices[normed_value]

        ip_address, _, port = normed_value.rpartition(":")

        try:
            ip_address = (
                ipaddress.ip_address(ip_address.strip("[]"))
                if ip_address != "localhost"
                else "localhost"
            )
            port = int(port)
            assert port > 0
        except:
            self.fail(
                f"invalid choice: {value}. (choose from {', '.join(self.choices)})",
                param,
                ctx,
            )

        return f"{ip_address}:{port}"


@cli.command()
@click.pass_context
@click.option(
    "--controller",
    prompt=True,
    is_eager=True,
    required=True,
    type=click.Choice(["terminal", "chrome"]),
    default="chrome",
)
@click.option(
    "--navigator",
    prompt=True,
    is_eager=True,
    required=True,
    type=click.Choice(["terminal", "chrome"]),
    default="chrome",
)
@click.option(
    "--informant",
    prompt=True,
    is_eager=True,
    required=True,
    type=click.Choice(["terminal", "chrome"]),
    default="terminal",
)
@click.option(
    "--chrome",
    prompt=True,
    type=ChromeChoice(),
    cls=Mutex,
    not_required_if=["controller=terminal", "navigator=terminal", "informant=terminal"],
    default="launch",
)
@click.argument("datamine", type=click.Path(exists=True, readable=True))
@coroutine
async def curate(ctx, datamine, controller, navigator, informant, chrome=None):
    # TODO: Move chrome parsing into method so we don't rely on eager anymore

    async with PyppeteerLauncher(chrome) as launcher:
        Controller = {
            "terminal": TerminalController,
            "chrome": launcher.warp(PyppeteerController),
        }[controller]
        Navigator = {
            "terminal": TerminalNavigator,
            "chrome": launcher.warp(PyppeteerNavigator),
        }[navigator]
        Informant = {
            "terminal": TerminalFormatter,
            "chrome": launcher.warp(PyppeteerFormatter),
        }[informant]

        await curation.curate(
            ctx_registry(ctx), Datamine(datamine), Controller, Navigator, Informant
        )


# @curate.command()
# @click.pass_context
# @coroutine
# async def terminal(ctx):
#    """
#    Runs the interactive curation process in the terminal.
#    """
#    await curation.curate(
#        ctx_registry(ctx),
#        ctx.obj["datamine"],
#        curation.TerminalController,
#        curation.TerminalFormatter,
#    )


# @curate.command()
# @click.pass_context
# @coroutine
# async def launch(ctx):
#    """
#    Runs the interactive curation process in a Chrome browser.
#    Launches a new Chrome browser instances.
#    The browser will automatically be closed once the curation session finished.
#    """
#    await curation.curate(
#        ctx_registry(ctx),
#        ctx.obj["datamine"],
#        curation.PyppeteerController.Launch,
#        curation.PyppeteerFormatter,
#    )


# @curate.command()
# @click.pass_context
# @click.argument("address")
# @coroutine
# async def connect(ctx, address):
#    """
#    Runs the interactive curation process in a Chrome browser.
#    Connects to a running Chrome browser instance at ADDRESS.
#    The browser will not automatically be closed once the curation session finished.
#    ADDRESS is an IPv4 'IP:PORT' or IPv6 '[IP]:PORT' address.
#    You can launch a new Chrome browser using\n
#     > chrome --remote-debugging-port=PORT
#    """
#    await curation.curate(
#        ctx_registry(ctx),
#        ctx.obj["datamine"],
#        curation.PyppeteerController.Connect(address),
#        curation.PyppeteerFormatter,
#    )


if __name__ == "__main__":
    cli(prog_name="cmd-iaso")
