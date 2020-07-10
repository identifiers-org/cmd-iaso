import io

import click

from ..utils import format_json

from .generator import CurationDirection
from .interact import CurationController, CurationNavigator, CurationFormatter
from ..click.aprompt import aprompt


class TerminalController(CurationController):
    async def prompt(self):
        direction = await aprompt(
            "Continue curation",
            type=click.Choice(CurationController.CHOICES.keys()),
            default=next(
                k
                for k, v in TerminalController.CHOICES.items()
                if v == CurationDirection.FORWARD
            ),
        )

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
    def __init__(self):
        self.buffer = []

    def format_json(self, title, content, level):
        self.buffer.append((title, content, level))

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

        for title, content, level in self.buffer:
            output.append("- {}: ".format(click.style(title, underline=True)))
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
