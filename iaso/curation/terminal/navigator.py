import click

from ..interact import CurationNavigator


class TerminalNavigator(CurationNavigator):
    async def navigate(self, url, institution_name):
        ctx = click.get_current_context()

        center_str = "_" * len(url)

        click.echo(
            ">>> {} <<<".format(center_str)
            .center(80 if ctx.max_content_width is None else ctx.max_content_width)
            .replace(center_str, click.style(url, fg="bright_blue", underline=True))
        )
