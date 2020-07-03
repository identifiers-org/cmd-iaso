import gzip
import json
import math

from itertools import zip_longest

from tqdm import tqdm

from .institution_entity_extraction import greedily_extract_institution_entities
from .institution_entity_linking import query_institution_entity_details

DETAILS_CHUNK_SIZE = 10


def chunk(iterable, chunksize, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"

    args = [iter(iterable)] * chunksize

    return zip_longest(*args, fillvalue=fillvalue)


def deduplicate_registry_institutions(registry, academine_path):
    extracted_institution_entities = {
        iid: greedily_extract_institution_entities(institution.name)
        for iid, institution in tqdm(
            list(registry.institution.items())[:20],
            desc="Extracting institution entities",
        )
    }

    deduped_institution_entities = set(
        entity
        for entities in extracted_institution_entities.values()
        for entity in entities
    )

    institution_entity_details = dict()

    for entities in tqdm(
        chunk(deduped_institution_entities, DETAILS_CHUNK_SIZE),
        total=int(math.ceil(len(deduped_institution_entities) / DETAILS_CHUNK_SIZE)),
        desc="Fetching institution details",
    ):
        institution_entity_details.update(query_institution_entity_details(entities))

    institutions = []

    for iid, entities in extracted_institution_entities.items():
        institution_entities = []

        for entity in entities:
            institution_entity = {
                k: v
                for k, v in institution_entity_details[entity].items()
                if v is not None
            }

            if len(institution_entity) > 0:
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
