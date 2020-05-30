from ...json_schema_file import JsonSchemaFile


def ScrapingJobs(filepath):
    return JsonSchemaFile(filepath, "JOBS", ScrapingJobs.SCHEMA)


ScrapingJobs.SCHEMA = {
    "type": "array",
    "items": {
        "type": "array",
        "items": [{"type": "number"}, {"type": "string"}, {"type": "string"}],
        "additionalItems": False,
    },
    "additionalItems": False,
}
