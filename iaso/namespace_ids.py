from .json_schema_file import JsonSchemaFile


def NamespaceIds(filepath):
    return JsonSchemaFile(
        filepath, "NAMESPACE_IDS", NamespaceIds.SCHEMA, namedtuple=False
    )


NamespaceIds.SCHEMA = {
    "type": "object",
    "additionalProperties": {"type": "array", "items": {"type": ["string", "null"]},},
}
