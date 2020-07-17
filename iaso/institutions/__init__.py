import asyncio
import gzip
import json

from itertools import zip_longest

from tqdm import tqdm

from .wikidataclient import WikiDataClient
from .entity.matching import greedily_match_institution_entities
from .entity.linking import query_institution_entity_details

DETAILS_CHUNK_SIZE = 10


def chunk(iterable, chunksize, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"

    args = [iter(iterable)] * chunksize

    return zip_longest(*args, fillvalue=fillvalue)


async def deduplicate_registry_institutions(registry, academine_path):
    client = WikiDataClient()

    async def collect_extracted_institution_entities(
        client, institution_string, iid, progress, extracted_institution_entities
    ):
        extracted_institution_entities[iid] = await greedily_match_institution_entities(
            client, institution_string
        )

        progress.update()
        progress.set_postfix(ordered_dict=client.backoff)

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
                for iid, institution in registry.institution.items()
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
            institution_entity = {"uuid": entity, "matches": tuple(matches)}

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
