import asyncio
import json

import click

from jsonschema import validate

from ...click.aprompt import aprompt


class TerminalTagController:
    IGNORE = "ignore"
    TAGS = "tags"

    TAGS_SCHEMA = {
        "type": "array",
        "items": {"type": "string"},
        "additionalItems": False,
    }

    ALL_TAGS_SCHEMA = {
        "type": "object",
        "patternProperties": {
            r"^\[[1-9][0-9]*\]$": TAGS_SCHEMA,
        },
        "additionalProperties": False,
    }

    def __init__(self, informant):
        self.informant = informant

        self.prompt_tags_future = None

        click.get_current_context().obj["terminal_tag_controller"] = self

    async def prompt_tags(self):
        if self.prompt_tags_future is not None:
            return

        self.prompt_tags_future = asyncio.create_task(self.prompt_tags_impl())

    async def prompt_tags_impl(self):
        decision = await aprompt(
            "Modify tags",
            type=click.Choice((self.TAGS, self.IGNORE)),
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

    async def edit_tags(self, tags, schema):
        result = click.edit(json.dumps(tags, indent=2), extension=".json")

        if result is None:
            return None

        try:
            json_result = json.loads(result)
        except json.JSONDecodeError as err:
            click.echo(
                click.style(f"Error modifying the tags (invalid JSON): {err}", fg="red")
            )

            return None

        try:
            validate(instance=json_result, schema=schema)
        except Exception as err:
            click.echo(
                click.style(
                    f"Error modifying the tags (does not match expected schema): {err.message} at ROOT{''.join(f'[{repr(attr)}]' for attr in err.absolute_path)}",
                    fg="red",
                )
            )

            return None

        return json_result

    async def edit_all_tags(self):
        new_all_tags = await self.edit_tags(
            {
                k: self.informant.tag_store.get_tags_for_identifier(v)
                for k, v in self.informant.tags_mapping.items()
            },
            self.ALL_TAGS_SCHEMA,
        )

        if new_all_tags is not None:
            for k, v in new_all_tags.items():
                identifier = self.informant.tags_mapping.get(k)

                if identifier is not None:
                    self.informant.tag_store.set_tags_for_identifier(identifier, v)

    async def edit_ignored_tags(self):
        new_ignored_tags = await self.edit_tags(
            self.informant.ignored_tags, self.TAGS_SCHEMA
        )

        if new_ignored_tags is not None:
            self.informant.ignored_tags = new_ignored_tags
