import gzip
import json

import click

from jsonschema import validate

from .jsondb import json_to_namedtuple


def Datamine(filepath):
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
        validate(instance=json_file, schema=Datamine.SCHEMA)
    except Exception as err:
        raise click.FileError(
            filepath,
            hint=click.style(
                "JSON file does not match the DATAMINE schema ({message} at ROOT{path})".format(
                    message=err.message,
                    path="".join(f"[{repr(attr)}]" for attr in err.absolute_path),
                ),
                fg="red",
            ),
        )

    return json_to_namedtuple(json_file)


Datamine.SCHEMA = {
    "type": "object",
    "properties": {
        "environment": {
            "type": "object",
            "properties": {
                "machine": {"type": "string"},
                "os": {"type": "string"},
                "cpu": {"type": "string"},
                "cores": {"type": "string"},
                "memory": {"type": "string"},
                "storage": {"type": "string"},
                "cmd": {"type": "string"},
            },
            "required": [],
            "additionalProperties": False,
        },
        "providers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "number"},
                    "pings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "lui": {"type": "string"},
                                "date": {"type": "string"},
                                "redirects": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "url": {"type": ["string", "null"]},
                                            "ip_port": {"type": ["string", "null"]},
                                            "response_time": {
                                                "type": ["number", "null"]
                                            },
                                            "status": {"type": ["number", "null"]},
                                            "dns_error": {"type": "boolean"},
                                            "ssl_error": {"type": "boolean"},
                                            "invalid_response": {"type": "boolean"},
                                        },
                                        "required": [
                                            "url",
                                            "ip_port",
                                            "response_time",
                                            "status",
                                            "dns_error",
                                            "ssl_error",
                                            "invalid_response",
                                        ],
                                        "additionalProperties": False,
                                    },
                                },
                                "features": {
                                    "type": "string",
                                    "contentEncoding": "base64",
                                },
                            },
                            "required": ["lui", "date", "redirects"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["id", "pings"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["environment", "providers"],
    "additionalProperties": False,
}
