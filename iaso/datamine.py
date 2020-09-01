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
                    "id": {"type": "integer", "minimum": 0},
                    "pings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "lui": {"type": "string"},
                                "random": {"type": "boolean"},
                                "date": {"type": "string"},
                                "redirects": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "url": {"type": ["string", "null"]},
                                            "ip_port": {"type": ["string", "null"]},
                                            "response_time": {
                                                "type": ["integer", "null"]
                                            },
                                            "status": {"type": ["integer", "null"]},
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
                                "empty_content": {"type": "boolean"},
                            },
                            "required": [
                                "lui",
                                "random",
                                "date",
                                "redirects",
                                "empty_content",
                            ],
                            "additionalProperties": False,
                        },
                        "additionalItems": False,
                    },
                    "analysis": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "properties": {
                                "lui": {"type": "string"},
                                "information_content": {
                                    "type": "number",
                                    "minimum": 0.0,
                                    "maximum": 1.0,
                                },
                                "length": {"type": "integer", "minimum": 0},
                                "noise": {"type": "integer", "minimum": 0},
                            },
                            "required": [
                                "lui",
                                "information_content",
                                "noise",
                                "length",
                            ],
                            "additionalProperties": False,
                        },
                        "additionalItems": False,
                    },
                },
                "required": ["id", "pings", "analysis"],
                "additionalProperties": False,
            },
            "additionalItems": False,
        },
    },
    "required": ["environment", "providers"],
    "additionalProperties": False,
}
