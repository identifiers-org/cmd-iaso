import gzip
import json

import click

from jsonschema import validate

from .jsondb import json_to_namedtuple


def JsonSchemaFile(filepath, schemaname, schema, namedtuple=True):
    try:
        if filepath.endswith(".gz"):
            with click.open_file(filepath, "rb") as file:
                with gzip.GzipFile(fileobj=file, mode="r") as file:
                    json_file = json.load(file)
        else:
            with click.open_file(filepath, "r") as file:
                json_file = json.load(file)
    except Exception as err:
        print(repr(err))

        raise click.FileError(
            filepath, hint=click.style(f"Not a valid GZIP file ({err})", fg="red")
        )
    except json.JSONDecodeError as err:
        raise click.FileError(
            filepath, hint=click.style(f"Not a valid JSON file ({err})", fg="red")
        )

    try:
        validate(instance=json_file, schema=schema)
    except Exception as err:
        raise click.FileError(
            filepath,
            hint=click.style(
                "JSON file does not match the {name} schema ({message} at ROOT{path})".format(
                    name=schemaname,
                    message=err.message,
                    path="".join(f"[{repr(attr)}]" for attr in err.absolute_path),
                ),
                fg="red",
            ),
        )

    return json_to_namedtuple(json_file) if namedtuple else json_file
