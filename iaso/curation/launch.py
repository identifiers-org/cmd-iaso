import os

from functools import partial

import click

from ..click.lazy import lazy_import
from ..click.registry import ensure_registry
from .pyppeteer import PyppeteerLauncher
from .tag_store import TagStore

lazy_import(
    globals(),
    """
from .pyppeteer.informant import PyppeteerInformant
from .pyppeteer.controller import PyppeteerController

from .statistics import (
    StatisticsController,
    StatisticsNavigator,
    StatisticsInformant
)

from .terminal.controller import TerminalController
from .terminal.informant import TerminalInformant
from .terminal.navigator import TerminalNavigator
""",
)


async def launch_curation(
    curation_func,
    ChromeNavigator,
    ctx,
    statistics,
    controller,
    navigator,
    informant,
    chrome,
    tags,
    ignored_tags,
    session,
):
    if not os.path.exists(tags):
        click.confirm(
            f"{tags} does not exist yet. Do you want to start with a new cross-session tags store?",
            abort=True,
        )

        tag_store = TagStore(tags)
    else:
        tag_store = TagStore.load_from_file(tags)

    async with PyppeteerLauncher(chrome) as launcher:
        Controller = (
            {
                "terminal": partial(
                    TerminalController, control_tags=(informant != "chrome")
                ),
                "chrome": launcher.warp(
                    partial(
                        PyppeteerController,
                        url_regex=(None if navigator == "chrome" else r"^.*$"),
                    )
                ),
            }[controller]
            if not statistics
            else StatisticsController
        )
        Navigator = (
            {
                "terminal": TerminalNavigator,
                "chrome": launcher.warp(ChromeNavigator),
            }[navigator]
            if not statistics
            else StatisticsNavigator
        )
        Informant = (
            {
                "terminal": partial(
                    TerminalInformant,
                    ignored_tags,
                    control_tags=(controller != "terminal"),
                ),
                "chrome": launcher.warp(
                    partial(
                        PyppeteerInformant,
                        ignored_tags,
                        url_regex=(None if navigator == "chrome" else r"^.*$"),
                    )
                ),
            }[informant]
            if not statistics
            else partial(StatisticsInformant, ignored_tags)
        )

        if statistics:
            session.reset()
            session.discard()

        await curation_func(
            ensure_registry(ctx),
            Controller,
            Navigator,
            Informant,
            tag_store,
            session,
        )
