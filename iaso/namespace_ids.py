from .json_schema_file import JsonSchemaFile


def NamespaceIds(filepath):
    return JsonSchemaFile(filepath, "NAMESPACE_IDS", NamespaceIds.SCHEMA)


NamespaceIds.SCHEMA = {
    "type": "object",
    "patternProperties": {
        "^[A-Za-z_][A-Za-z0-9_]*$": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}
