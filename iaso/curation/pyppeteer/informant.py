import asyncio
import json
import re

import pyppeteer

from contextlib import suppress

from ..interact import CurationFormatter
from .coordinator import PyppeteerCoordinator


class PyppeteerFormatter(CurationFormatter):
    def __init__(self, page, tag_store, ignored_tags=[], url_regex=None):
        self.page = page

        self.tag_store = tag_store

        self.url_regex_pattern = url_regex if url_regex is not None else r"^{$url}.*$"
        self.url_regex = re.compile(self.url_regex_pattern)

        self.lock = asyncio.Lock()

        self.buffer = []

        self.title_type = ""
        self.title_text = ""
        self.description = ""
        self.entity_index = ""
        self.issues = []
        self.tags_mapping = dict()

        self.ignored_tags = ignored_tags

    async def __aenter__(self):
        self.page.on("framenavigated", self.onnavigate)
        self.page.on("console", self.onconsole)

        return self

    async def onnavigate(self, frame):
        await self.refresh(False)

    def format_json(self, identifier, title, content, level):
        self.buffer.append((identifier, title, content, level))

    def check_if_non_empty_else_reset(self):
        for identifier, title, content, level in self.buffer:
            tags = self.tag_store.get_tags_for_identifier(identifier)

            if any(tag in self.ignored_tags for tag in tags):
                continue

            return True

        self.buffer.clear()

        return False

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

                issues = []

                self.tags_mapping.clear()

                for i, (identifier, title, content, level) in enumerate(self.issues):
                    tags = self.tag_store.get_tags_for_identifier(identifier)

                    if any(tag in self.ignored_tags for tag in tags):
                        continue

                    issues.append((title, content, level, tags))
                    self.tags_mapping[f"[{i+1}]"] = identifier

                await coordinator.evaluate(
                    "informant.js",
                    self.url_regex.match(self.page.url) is not None,
                    display_overlay,
                    self.title_type,
                    self.title_text,
                    self.description,
                    self.entity_index,
                    issues,
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
                identifier = self.tags_mapping.get(identifier)

                if identifier is not None:
                    self.tag_store.set_tags_for_identifier(identifier, tags)
