import gzip
import json

import click

from ..json_schema_file import JsonSchemaFile
from ..datamine import Datamine
from ..jsondb import namedtuple_to_dict


class CurationSession:
    SCHEMA = {
        "type": "object",
        "properties": {
            "datamine": Datamine.SCHEMA,
            "validators": {
                "type": "array",
                "items": {"type": "string"},
                "additionalItems": False,
            },
            "position": {"type": "number"},
            "visited": {
                "type": "array",
                "items": {"type": "number"},
                "additionalItems": False,
            },
        },
        "additionalProperties": False,
    }

    @staticmethod
    def load_from_file(filepath, validate_validators):
        session = JsonSchemaFile(filepath, "SESSION", CurationSession.SCHEMA)

        return CurationSession(
            filepath,
            session.datamine,
            validate_validators(session.validators),
            session.position,
            set(session.visited),
        )

    def __init__(self, filepath, datamine, validators, position, visited):
        self.__filepath = filepath
        self.__datamine = datamine
        self.__validators = validators
        self.__position = position
        self.__visited = visited

        click.get_current_context().call_on_close(self.save)

    @property
    def datamine(self):
        return self.__datamine

    @property
    def validators(self):
        return self.__validators

    @property
    def position(self):
        return self.__position

    @property
    def visited(self):
        return self.__visited

    def update(self, position, visited):
        self.__position = position
        self.__visited = self.__visited.union(visited)

    def save(self):
        if self.__filepath is not None:
            click.echo(
                click.style(
                    f"Saving the current curation session to {self.__filepath} ...",
                    fg="yellow",
                )
            )

            with gzip.open(self.__filepath, "wt") as file:
                json.dump(
                    {
                        "datamine": namedtuple_to_dict(self.__datamine),
                        "validators": list(self.__validators.keys()),
                        "position": self.__position,
                        "visited": list(self.__visited),
                    },
                    file,
                )
        else:
            click.echo(
                click.style(
                    f"The current curation session has been discarded.", fg="yellow"
                )
            )