import asyncio
import io
import json

from collections import OrderedDict

import click

from ..utils import format_json

from .generator import CurationDirection
from .interact import CurationController, CurationNavigator, CurationFormatter
from ..click.aprompt import aprompt


class TerminalController(CurationController):
    def __init__(self, control_tags=False):
        self.choices = list(CurationController.CHOICES.keys())

        if control_tags:
            self.choices.extend((TerminalFormatter.TAGS, TerminalFormatter.IGNORE))

    async def prompt(self):
        while True:
            direction = await aprompt(
                "Continue curation",
                type=click.Choice(self.choices),
                default=next(
                    k
                    for k, v in TerminalController.CHOICES.items()
                    if v == CurationDirection.FORWARD
                ),
            )

            if direction == TerminalFormatter.IGNORE:
                await click.get_current_context().obj[
                    "tags_formatter"
                ].edit_ignored_tags()
            elif direction == TerminalFormatter.TAGS:
                await click.get_current_context().obj["tags_formatter"].edit_all_tags()
            else:
                return TerminalController.CHOICES[direction]


class TerminalNavigator(CurationNavigator):
    async def navigate(self, url, institution_name):
        ctx = click.get_current_context()

        center_str = "_" * len(url)

        click.echo(
            ">>> {} <<<".format(center_str)
            .center(80 if ctx.max_content_width is None else ctx.max_content_width)
            .replace(center_str, click.style(url, fg="bright_blue", underline=True))
        )


class TerminalFormatter(CurationFormatter):
    IGNORE = "ignore"
    TAGS = "tags"

    def __init__(self, tag_store, ignored_tags=[], control_tags=True):
        self.tag_store = tag_store

        self.ignored_tags = ignored_tags
        self.control_tags = control_tags

        self.prompt_tags_future = None

        click.get_current_context().obj["tags_formatter"] = self

        self.buffer = []
        self.tags_mapping = dict()

    def format_json(self, identifier, title, content, level):
        self.buffer.append((identifier, title, content, level))

    async def output(self, url, title, description, position, total):
        ctx = click.get_current_context()

        output = []

        output.append(
            " {} / {} ".format(position + 1, total).center(
                80 if ctx.max_content_width is None else ctx.max_content_width, "="
            )
        )

        output.append(
            "\n{}{}{}\n".format(
                click.style(f"Curation required for {title['type']} ", fg="yellow"),
                click.style(title["text"], fg="yellow", bold=True),
                click.style(":", fg="yellow"),
            )
        )

        output.append(f"{description}\n")

        self.tags_mapping.clear()

        for i, (identifier, title, content, level) in enumerate(self.buffer):
            tags = self.tag_store.get_tags_for_identifier(identifier)

            if any(tag in self.ignored_tags for tag in tags):
                continue

            output.append(f"- [{i+1}] {click.style(title, underline=True)}: ")

            self.tags_mapping[f"[{i+1}]"] = identifier

            analysed_tags = [(tag, tag in self.ignored_tags) for tag in tags]

            if isinstance(content, str):
                output.append(format_json(content, indent=1))
                output.append("\n")
                output.append(
                    f"  {click.style('tags', fg='red')}: [{', '.join(click.style(tag, fg=('green' if ignored else 'yellow')) for tag, ignored in tags)}]"
                )
            else:
                content = dict(
                    tags=[
                        {
                            "__rich__": True,
                            "text": tag,
                            "fg": "green" if ignored else "yellow",
                            "bold": ignored,
                        }
                        for tag, ignored in analysed_tags
                    ],
                    **content,
                )
                output.append(format_json(content, indent=1))

            output.append("\n")

        output.append(
            " {} / {} ".format(position + 1, total).center(
                80 if ctx.max_content_width is None else ctx.max_content_width, "="
            )
        )

        output = "".join(output)

        try:
            click.echo(output)
        except io.BlockingIOError:
            click.echo_via_pager(output)
            click.echo(
                "{}... Switching to pager ...".format(
                    click.style(" \b", fg="black", underline=True)
                )
            )

        self.buffer.clear()

        if self.control_tags:
            await self.prompt_tags()

    async def prompt_tags(self):
        if self.prompt_tags_future is not None:
            return

        self.prompt_tags_future = asyncio.create_task(self.prompt_tags_impl())

    async def prompt_tags_impl(self):
        decision = await aprompt(
            "Modify tags", type=click.Choice((self.TAGS, self.IGNORE)),
        )

        if decision == self.IGNORE:
            await self.edit_ignored_tags()
        elif decision == self.TAGS:
            await self.edit_all_tags()

        self.prompt_tags_future = asyncio.create_task(self.prompt_tags_impl())

    def cancel_prompt_tags(self):
        if self.prompt_tags_future is not None:
            self.prompt_tags_future.cancel()

            click.echo("")
            ctx = click.get_current_context()
            click.echo(
                "=" * (80 if ctx.max_content_width is None else ctx.max_content_width)
            )

            self.prompt_tags_future = None

    async def edit_tags(self, tags):
        result = click.edit(json.dumps(tags, indent=2), extension=".json")

        if result is None:
            return None

        try:
            return json.loads(result)
        except json.JSONDecodeError as err:
            click.echo(click.style(f"Error modifying the tags: {err}", fg="red"))

        return None

    # TODO: should we check a schema here???

    async def edit_all_tags(self):
        new_all_tags = await self.edit_tags(
            {
                k: self.tag_store.get_tags_for_identifier(v)
                for k, v in self.tags_mapping.items()
            }
        )

        if new_all_tags is not None:
            for k, v in new_all_tags.items():
                identifier = self.tags_mapping.get(k)

                if identifier is not None:
                    self.tag_store.set_tags_for_identifier(identifier, v)

    async def edit_ignored_tags(self):
        new_ignored_tags = await self.edit_tags(self.ignored_tags)

        if new_ignored_tags is not None:
            self.ignored_tags = new_ignored_tags
