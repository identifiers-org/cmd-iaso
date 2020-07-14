import asyncio
import re

import click
import pyppeteer

from contextlib import suppress

from ..interact import CurationController
from ..generator import CurationDirection
from .coordinator import PyppeteerCoordinator


class PyppeteerController(CurationController):
    def __init__(self, page, url_regex=None):
        self.page = page
        self.url_regex = re.compile(
            url_regex
            if url_regex is not None
            else r"^https:\/\/registry\.identifiers\.org.*$"
        )

        self.lock = asyncio.Lock()

        self.prompt_future = None

    async def __aenter__(self):
        self.page.on("framenavigated", self.onnavigate)
        self.page.on("console", self.onconsole)

        await self.refresh()

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.prompt_future = None

    async def onnavigate(self, frame):
        await self.refresh()

    async def refresh(self):
        async with PyppeteerCoordinator(self.page) as coordinator:
            with suppress(pyppeteer.errors.NetworkError):
                await coordinator.addStyleTagWithId("iaso.css", "iaso-style")
                await coordinator.addStyleTagWithId("header.css", "iaso-header-style")

                await coordinator.evaluate("header.js")

                await coordinator.evaluate(
                    "controller.js",
                    self.url_regex.match(self.page.url) is not None,
                    *CurationController.CHOICES.keys()
                )

    def onconsole(self, console):
        if (
            console.type == "info"
            and console.text.startswith("iaso-controller-")
            and console.text[16:] in CurationController.CHOICES
        ):
            if self.prompt_future is not None:
                tags_formatter = click.get_current_context().obj.get("tags_formatter")

                if tags_formatter is not None:
                    tags_formatter.cancel_prompt_tags()

                self.prompt_future.set_result(
                    CurationController.CHOICES[console.text[16:]]
                )

    async def prompt(self):
        self.prompt_future = asyncio.Future()

        prompt = await self.prompt_future

        self.prompt_future = None

        return prompt
