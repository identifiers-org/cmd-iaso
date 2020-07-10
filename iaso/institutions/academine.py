from collections import namedtuple

from ..json_schema_file import JsonSchemaFile


def Academine(filepath):
    return JsonSchemaFile(
        filepath,
        "ACADEMINE",
        Academine.SCHEMA,
        classes={
            "entities": namedtuple(
                "Entity",
                ["matches", "name", "homeUrl", "description", "rorId", "location"],
            )
        },
    )


Academine.SCHEMA = {
    "type": "object",
    "properties": {
        "institutions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "minimum": 0},
                    "string": {"type": "string"},
                    "entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "uuid": {"type": "string"},
                                "matches": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "additionalItems": False,
                                },
                                "name": {"type": ["string", "null"]},
                                "homeUrl": {"type": ["string", "null"]},
                                "description": {"type": ["string", "null"]},
                                "rorId": {"type": ["string", "null"]},
                                "location": {
                                    "type": ["object", "null"],
                                    "properties": {
                                        "countryCode": {"type": "string"},
                                        "countryName": {"type": "string"},
                                    },
                                    "required": ["countryCode", "countryName"],
                                    "additionalProperties": False,
                                },
                            },
                            "required": ["matches"],
                            "additionalProperties": False,
                        },
                        "additionalItems": False,
                    },
                },
                "required": ["id", "string", "entities"],
                "additionalProperties": False,
            },
            "additionalItems": False,
        },
    },
    "required": ["institutions"],
    "additionalProperties": False,
}
