import io
import gzip
import json

import click

from jsonschema import validate

from .jsondb import json_to_namedtuple


def JsonSchemaFile(filepath, schemaname, schema, namedtuple=True):
    with click.open_file(filepath, "rb") as file:
        content = file.read()

    try:
        try:
            binary_file = io.BytesIO(content)

            gzip_file = False

            with gzip.GzipFile(fileobj=binary_file, mode="r") as file:
                # Force gzip to start decompressing
                file.peek(1)

                gzip_file = True

                json_file = json.load(file)
        except json.JSONDecodeError as err:
            raise err
        except Exception as err:
            # If gzip_file is False, the file is not a GZIP file so we should
            #  try reading it as a normal text file
            if gzip_file:
                raise click.FileError(
                    filepath,
                    hint=click.style(f"Not a valid GZIP file ({err})", fg="red"),
                )

            text_file = io.StringIO(content.decode("utf-8"))

            json_file = json.load(text_file)
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
