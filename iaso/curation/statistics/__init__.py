import json

from collections import Counter

import click

from ..generator import CurationDirection
from ..interact import CurationController, CurationNavigator, CurationInformant
from .report import report_statistics


class StatisticsController(CurationController):
    def __init__(self):
        self.position = -1
        self.direction = CurationDirection.FORWARD

        click.get_current_context().obj["statistics_controller"] = self

    async def prompt(self):
        return self.direction


class StatisticsNavigator(CurationNavigator):
    async def navigate(self, url, auxiliary):
        pass


class StatisticsInformant(CurationInformant):
    def __init__(self, ignored_tags, tag_store):
        super().__init__(ignored_tags, tag_store)

        self.ok_entries = 0
        self.ig_entries = 0

        self.ok_issues = Counter()
        self.ig_issues = Counter()

    def check_if_non_empty_else_reset(self):
        result = False

        for identifier, title, content, level in self.buffer:
            try:
                issue_type = json.loads(identifier)["type"]
            except (json.JSONDecodeError, KeyError):
                issue_type = "Unidentified"

            tags = self.tag_store.get_tags_for_identifier(identifier)

            if any(tag in self.ignored_tags for tag in tags):
                self.ig_issues[issue_type] += 1

                continue

            self.ok_issues[issue_type] += 1

            result = True

        if result:
            self.ok_entries += 1
        else:
            self.ig_entries += 1

        self.buffer.clear()

        return result

    async def output(self, url, title, description, position, total):
        controller = click.get_current_context().obj["statistics_controller"]

        if position <= controller.position:
            controller.direction = CurationDirection.FINISH

        controller.position = position

    async def __aexit__(self, exc_type, exc_value, traceback):
        report_statistics(
            self.ok_entries, self.ig_entries, self.ok_issues, self.ig_issues
        )
