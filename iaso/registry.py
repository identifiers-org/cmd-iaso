import requests

from .jsondb import json_to_dict_db


def Registry():
    with requests.get(
        "https://registry.api.identifiers.org/resolutionApi/getResolverDataset",
        allow_redirects=True,
        timeout=10,
    ) as r:
        return json_to_dict_db(r.json()["payload"], "Registry")
