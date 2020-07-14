import asyncio
import json
import re

import pyppeteer

from contextlib import suppress

from ..interact import CurationFormatter
from .coordinator import PyppeteerCoordinator


class PyppeteerFormatter(CurationFormatter):
    def __init__(self, page, ignored_tags=[], url_regex=None):
        self.page = page

        self.url_regex_pattern = url_regex if url_regex is not None else r"^{$url}.*$"
        self.url_regex = re.compile(self.url_regex_pattern)

        self.lock = asyncio.Lock()

        self.buffer = []

        self.title_type = ""
        self.title_text = ""
        self.description = ""
        self.entity_index = ""
        self.issues = []

        self.ignored_tags = ignored_tags

    async def __aenter__(self):
        self.page.on("framenavigated", self.onnavigate)
        self.page.on("console", self.onconsole)

        return self

    async def onnavigate(self, frame):
        await self.refresh(False)

    def format_json(self, title, content, level):
        self.buffer.append((title, content, level, ["some", "example", "tags"]))

    async def output(self, url, title, description, position, total):
        if "{$url}" in self.url_regex_pattern:
            self.url_regex = re.compile(
                self.url_regex_pattern.replace("{$url}", re.escape(url))
            )

        self.title_type = title["type"]
        self.title_text = title["text"]
        self.description = description
        self.entity_index = "({} / {})".format(position + 1, total)
        self.issues = self.buffer

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
                    "renderjson.js", "iaso-informant-renderjson-script",
                )

                await coordinator.addStyleTagWithId(
                    "tags.css", "iaso-informant-tags-style"
                )

                await coordinator.addScriptTagWithId(
                    "tags.js", "iaso-informant-tags-script",
                )

                await coordinator.evaluate(
                    "informant.js",
                    self.url_regex.match(self.page.url) is not None,
                    display_overlay,
                    self.title_type,
                    self.title_text,
                    self.description,
                    self.entity_index,
                    self.issues,
                    self.ignored_tags,
                )

    def onconsole(self, console):
        if console.type == "info" and console.text.startswith("iaso-informant-tags"):
            try:
                separator = console.text.index("-", 20)

                identifier = console.text[20:separator]

                tags = json.loads(console.text[(separator + 1) :])
            except (ValueError, json.JSONDecodeError):
                return

            if identifier == "ignored":
                self.ignored_tags = tags
            else:
                print(f"Tags for {identifier}: {tags}")
