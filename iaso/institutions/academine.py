import click

from ..json_schema_file import JsonSchemaFile


def Academine(filepath):
    return JsonSchemaFile(filepath, "ACADEMINE", Academine.SCHEMA)


Datamine.SCHEMA = {
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
                                "matches": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "additionalItems": False,
                                },
                                "name": {"type": "string"},
                                "homeUrl": {"type": "string"},
                                "description": {"type": "string"},
                                "rorId": {"type": "string"},
                                "location": {
                                    "type": "object",
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
