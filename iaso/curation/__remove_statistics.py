import json

from collections import Counter
from textwrap import fill as wrap

import click

from .generator import CurationDirection
from .interact import CurationController, CurationNavigator, CurationInformant


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
        ctx = click.get_current_context()

        width = 80 if ctx.max_content_width is None else ctx.max_content_width

        title = "Curation Statistics"
        center_str = "_" * len(title)

        click.echo(
            " {} ".format(center_str)
            .center(width, "=")
            .replace(center_str, click.style(title, fg="green"))
        )

        click.echo()

        entries_str = (
            f"{self.ok_entries + self.ig_entries} "
            + f"entr{'y' if (self.ok_entries + self.ig_entries) == 1 else 'ies'}"
        )
        ignored_str = (
            "none"
            if self.ig_entries == 0
            else "one"
            if self.ig_entries == 1
            else self.ig_entries
        )

        click.echo(
            wrap(
                (
                    "In response to the current settings, {entries} {entries_were} "
                    + "identified for curation, {ignored} of which {ignored_were} ignored because "
                    + "of their issues' tags."
                ).format(
                    entries=entries_str,
                    entries_were=(
                        "was" if (self.ok_entries + self.ig_entries) == 1 else "were"
                    ),
                    ignored=ignored_str,
                    ignored_were=("was" if self.ig_entries == 1 else "were"),
                ),
                width=width,
            )
            .replace(entries_str, click.style(entries_str, fg="yellow"))
            .replace("curation", click.style("curation", fg="yellow"))
            .replace(ignored_str, click.style(ignored_str, fg="green"))
            .replace("ignored", click.style("ignored", fg="green"))
        )
        click.echo()

        click.echo(
            wrap("The following issue types were identified for curation:", width=width)
        )

        for issue_type, count in (self.ok_issues + self.ig_issues).most_common():
            ignored_str = f"{self.ig_issues[issue_type]} ignored"

            click.echo(
                wrap(
                    f"- {issue_type}: {count} ({ignored_str})",
                    width=width,
                    subsequent_indent="    ",
                )
                .replace(issue_type, click.style(issue_type, underline=True))
                .replace(str(count), click.style(str(count), fg="yellow"))
                .replace(ignored_str, click.style(ignored_str, fg="green"))
            )

        click.echo()

        click.echo(
            "=" * (80 if ctx.max_content_width is None else ctx.max_content_width)
        )
