import json

import click

from jsonschema import validate

from .jsondb import json_to_namedtuple


def Datamine(filepath):
    try:
        with click.open_file(filepath, "r") as file:
            json_file = json.load(file)
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
            ),
            fg="red",
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
                                "dns_error": {"type": "boolean"},
                                "redirects": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "url": {"type": "string"},
                                            "ip_port": {"type": "string"},
                                            "response_time": {"type": "number"},
                                            "status": {"type": "number"},
                                            "ssl_error": {"type": "boolean"},
                                            "invalid_response": {"type": "boolean"},
                                        },
                                        "required": ["url", "status"],
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
