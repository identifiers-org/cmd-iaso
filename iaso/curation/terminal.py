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
    async def navigate(self, url, provider_id):
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

    async def output(self, url, resource, namespace, position, total):
        ctx = click.get_current_context()

        click.echo(
            " {} / {} ".format(position + 1, total).center(
                80 if ctx.max_content_width is None else ctx.max_content_width, "="
            )
        )

        click.echo(
            "{}{}{}".format(
                click.style("Curation required for resource provider ", fg="yellow"),
                click.style(resource.name, fg="yellow", bold=True),
                click.style(":", fg="yellow"),
            )
        )

        click.echo("The following issues were observed:")

        for title, content, level in self.buffer:
            click.echo("- {}: ".format(click.style(title, underline=True)), nl=False)

            click.echo(format_json(content, indent=1))

        click.echo(
            " {} / {} ".format(position + 1, total).center(
                80 if ctx.max_content_width is None else ctx.max_content_width, "="
            )
        )

        self.buffer.clear()
