import io

import click

from ...format_json import format_json
from ..interact import CurationInformant
from .tag_controller import TerminalTagController


class TerminalInformant(CurationInformant):
    def __init__(self, ignored_tags, tag_store, control_tags=True):
        super().__init__(ignored_tags, tag_store)

        self.control_tags = control_tags

        self.tag_controller = TerminalTagController(self)

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

            output.append(format_json(content, indent=1))
            output.append("\n" if isinstance(content, str) else " ")
            output.append(
                f"{click.style('tagged with', fg='green')} {format_json(tags, indent=1)}"
            )

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
            await self.tag_controller.prompt_tags()
