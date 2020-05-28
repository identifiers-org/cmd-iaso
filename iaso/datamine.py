import click

from .json_schema_file import JsonSchemaFile


def Datamine(filepath):
    return JsonSchemaFile(filepath, "DATAMINE", Datamine.SCHEMA)


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
                                    "additionalItems": False,
                                },
                                "features": {
                                    "type": "string",
                                    "contentEncoding": "base64",
                                },
                            },
                            "required": ["lui", "date", "redirects"],
                            "additionalProperties": False,
                        },
                        "additionalItems": False,
                    },
                },
                "required": ["id", "pings"],
                "additionalProperties": False,
            },
            "additionalItems": False,
        },
    },
    "required": ["environment", "providers"],
    "additionalProperties": False,
}
