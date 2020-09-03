import gzip
import json

import click

from ..json_schema_file import JsonSchemaFile


class TagStore:
    SCHEMA = {
        "type": "object",
        "patternProperties": {
            r"^.+$": {
                "type": "array",
                "items": {"type": "string"},
                "additionalItems": False,
            },
        },
        "additionalProperties": False,
    }

    @staticmethod
    def load_from_file(filepath):
        store = JsonSchemaFile(filepath, "TAGSTORE", TagStore.SCHEMA, namedtuple=False)

        return TagStore(filepath, store)

    def __init__(self, filepath, store=dict()):
        self.filepath = filepath
        self.store = store

        click.get_current_context().call_on_close(self.save)

    def get_tags_for_identifier(self, identifier):
        return self.store.get(identifier, [])

    def set_tags_for_identifier(self, identifier, tags):
        self.store[identifier] = list(set(tags))

    def save(self):
        with gzip.open(self.filepath, "wt") as file:
            json.dump(self.store, file)

    @staticmethod
    def serialise_identity(json_value):
        return json.dumps(
            json_value,
            separators=(",", ":"),
            sort_keys=True,
        )
