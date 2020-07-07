import asyncio
import gzip
import json
import math

from itertools import zip_longest

import httpx

from tqdm import tqdm

from .institution_entity_extraction import greedily_extract_institution_entities
from .institution_entity_linking import query_institution_entity_details

DETAILS_CHUNK_SIZE = 10


def chunk(iterable, chunksize, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"

    args = [iter(iterable)] * chunksize

    return zip_longest(*args, fillvalue=fillvalue)


async def deduplicate_registry_institutions(registry, academine_path):
    client = httpx.AsyncClient(
        timeout=60, pool_limits=httpx.PoolLimits(max_keepalive=0, max_connections=5)
    )

    async def collect_extracted_institution_entities(
        client, institution_string, iid, progress, extracted_institution_entities
    ):
        extracted_institution_entities[
            iid
        ] = await greedily_extract_institution_entities(client, institution_string)

        progress.update()

    extracted_institution_entities = dict()

    with tqdm(
        total=len(registry.institution), desc="Extracting institution entities"
    ) as progress:
        await asyncio.gather(
            *[
                collect_extracted_institution_entities(
                    client,
                    institution.name,
                    iid,
                    progress,
                    extracted_institution_entities,
                )
                for iid, institution in list(registry.institution.items())[:20]
            ]
        )

    deduped_institution_entities = set(
        entity
        for entities in extracted_institution_entities.values()
        for entity in entities
    )

    async def collect_institution_entity_details(
        client, entities, progress, institution_entity_details
    ):
        institution_entity_details.update(
            await query_institution_entity_details(client, entities)
        )

        progress.update(len(entities))

    institution_entity_details = dict()

    with tqdm(
        total=len(deduped_institution_entities), desc="Fetching institution details"
    ) as progress:
        await asyncio.gather(
            *[
                collect_institution_entity_details(
                    client,
                    [entity for entity in entities if entity is not None],
                    progress,
                    institution_entity_details,
                )
                for entities in chunk(deduped_institution_entities, DETAILS_CHUNK_SIZE)
            ]
        )

    institutions = []

    for iid, entities in tqdm(
        extracted_institution_entities.items(), desc="Combining to ACADEMINE"
    ):
        institution_entities = []

        for entity, matches in entities.items():
            institution_entity = {"matches": tuple(matches)}

            institution_entity.update(
                (k, v)
                for k, v in institution_entity_details[entity].items()
                if v is not None
            )

            if len(institution_entity) > 1:
                institution_entities.append(institution_entity)

        institutions.append(
            {
                "id": iid,
                "string": registry.institution[iid].name,
                "entities": institution_entities,
            }
        )

    academine = {
        "institutions": institutions,
    }

    with gzip.open(academine_path, "wt") as file:
        json.dump(academine, file)
