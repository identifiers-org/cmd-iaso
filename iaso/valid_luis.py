import gzip
import json
import os

from collections import defaultdict
from json import JSONEncoder
from urllib.parse import urljoin, urlparse

import click
import requests

from tqdm import tqdm


class JSONSetEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return JSONEncoder.default(self, obj)


def validate_resolution_endpoint(resolution_endpoint):
    try:
        with requests.get(
            urljoin(resolution_endpoint, "/healthApi/liveness_check")
        ) as r:
            if r.status_code == requests.codes.ok:
                return
    except:
        pass

    raise click.UsageError(
        f"network error: could not connect to identifiers.org resolution endpoint at {resolution_endpoint}."
    )


def collect_namespace_ids_from_logs(logs, resolver, output):
    namespace_ids = defaultdict(set)

    filepaths = []

    for root, dirs, files in os.walk(logs):
        for filename in files:
            filepaths.append(os.path.join(root, filename))

    compact_ids = set()

    for filepath in tqdm(filepaths, desc="Reading logs"):
        try:
            with open(filepath, "r") as file:
                for line in file.readlines():
                    request = json.loads(line)
                    url = request["httpRequest"]["requestUrl"].strip()

                    if url.startswith("http://identifiers.org/"):
                        url = url[23:]
                    elif url.startswith("https://identifiers.org/"):
                        url = url[24:]
                    else:
                        continue

                    if ":" in url:
                        url = urlparse(f"http://identifiers.org/{url}").path

                    compact_ids.add(url.strip("/"))
        except:
            pass

    for c, compact_id in tqdm(
        enumerate(compact_ids), desc="Validating compact identifiers"
    ):
        with requests.get(urljoin(resolver, f"/{compact_id}")) as r:
            try:
                response = r.json()

                if response["errorMessage"] is not None:
                    continue

                compact_identifier = response["payload"].get("parsedCompactIdentifier")

                if (
                    compact_identifier is None
                    or compact_identifier["deprecatedNamespace"] is True
                ):
                    continue

                lui = compact_identifier["localId"]

                namespace_ids[compact_identifier["namespace"]].add(
                    lui[(lui.find(":") + 1) :]
                    if compact_identifier["namespaceEmbeddedInLui"]
                    else lui
                )
            except Exception as e:
                print(
                    "Error at {url}: {error}".format(
                        url=urljoin(resolver, f"/{compact_id}"), error=repr(e)
                    )
                )

        if ((c + 1) % 1000) == 0:
            with gzip.open(output, "wt") as file:
                json.dump(namespace_ids, file, cls=JSONSetEncoder)

    with gzip.open(output, "wt") as file:
        json.dump(namespace_ids, file, cls=JSONSetEncoder)

    num_luis = sum(len(ids) for ns, ids in namespace_ids.items())

    click.echo(
        click.style(
            f"{num_luis} valid LUIs were successfully extracted for {len(namespace_ids)} namespaces.",
            fg="green",
        )
    )
