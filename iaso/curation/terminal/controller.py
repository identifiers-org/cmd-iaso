import click

from ..generator import CurationDirection
from ..interact import CurationController
from ...click.aprompt import aprompt

from .tag_controller import TerminalTagController


class TerminalController(CurationController):
    def __init__(self, control_tags=False):
        self.choices = list(CurationController.CHOICES.keys())

        if control_tags:
            self.choices.extend(
                (TerminalTagController.TAGS, TerminalTagController.IGNORE)
            )

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

            if direction == TerminalTagController.IGNORE:
                await click.get_current_context().obj[
                    "terminal_tag_controller"
                ].edit_ignored_tags()
            elif direction == TerminalTagController.TAGS:
                await click.get_current_context().obj[
                    "terminal_tag_controller"
                ].edit_all_tags()
            else:
                return TerminalController.CHOICES[direction]
