import json

import click

from .jsondb import json_to_namedtuple


def Datamine(filepath):
    try:
        with click.open_file(filepath, "r") as file:
            return json_to_namedtuple(json.load(file))
    except Exception as err:
        raise click.FileError(filepath, hint=repr(err))
