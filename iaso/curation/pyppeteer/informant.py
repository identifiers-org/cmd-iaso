import asyncio
import re

import pyppeteer

from contextlib import suppress

from ..interact import CurationFormatter
from .coordinator import PyppeteerCoordinator


class PyppeteerFormatter(CurationFormatter):
    def __init__(self, page, url_regex=None):
        self.page = page

        self.url_regex_pattern = url_regex if url_regex is not None else r"^{$url}.*$"
        self.url_regex = re.compile(self.url_regex_pattern)

        self.lock = asyncio.Lock()

        self.buffer = []

        self.provider_name = ""
        self.provider_index = ""
        self.provider_issues = []

    async def __aenter__(self):
        self.page.on("framenavigated", self.onnavigate)

        return self

    async def onnavigate(self, frame):
        await self.refresh(False)

    def format_json(self, title, content):
        self.buffer.append((title, content))

    async def output(self, url, resource, namespace, position, total):
        if "{$url}" in self.url_regex_pattern:
            self.url_regex = re.compile(
                self.url_regex_pattern.replace("{$url}", re.escape(url))
            )

        self.provider_name = resource.name
        self.provider_index = "({} / {})".format(position + 1, total)
        self.provider_issues = self.buffer

        self.buffer = []

        await self.refresh(True)

    async def refresh(self, display_overlay):
        async with PyppeteerCoordinator(self.page) as coordinator:
            with suppress(pyppeteer.errors.NetworkError):
                await coordinator.addStyleTagWithId("iaso.css", "iaso-style")
                await coordinator.addStyleTagWithId("header.css", "iaso-header-style")

                await coordinator.evaluate("header.js")

                await coordinator.addStyleTagWithId(
                    "informant.css", "iaso-informant-style"
                )
                await coordinator.addStyleTagWithId(
                    "renderjson.css", "iaso-informant-renderjson-style"
                )

                await coordinator.addScriptTagWithId(
                    "../../../deps/renderjson/renderjson.js",
                    "iaso-informant-renderjson-script",
                )

                await coordinator.evaluate(
                    "informant.js",
                    self.url_regex.match(self.page.url) is not None,
                    display_overlay,
                    self.provider_name,
                    self.provider_index,
                    self.provider_issues,
                )
