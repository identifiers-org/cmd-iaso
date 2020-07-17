from collections import defaultdict
from enum import Enum, auto


class Entity(Enum):
    IRRELEVANT = auto()
    ORGANISATION = auto()
    LOCATION = auto()


async def fetch_wikidata_entity_types(client, wikidata_entities):
    query = (
        """SELECT DISTINCT ?entity ?superclass WHERE {
      VALUES ?entity { """
        + " ".join(f"wd:{qid}" for qid in wikidata_entities)
        + """ }

      ?entity wdt:P31 ?class.
      ?class wdt:P279* ?superclass.
    }"""
    )

    response = await client.query(query)

    entity_superclasses = defaultdict(set)

    for result in response["results"]["bindings"]:
        entity_superclasses[result["entity"]["value"][31:]].add(
            result["superclass"]["value"][31:]
        )

    entity_types = dict()

    for entity, superclasses in entity_superclasses.items():
        is_organisation = "Q43229" in superclasses
        is_location = "Q17334923" in superclasses
        is_territorial_entity = "Q1496967" in superclasses
        is_publication = "Q732577" in superclasses

        if is_organisation and not is_territorial_entity and not is_publication:
            entity_type = Entity.ORGANISATION
        elif is_location:
            entity_type = Entity.LOCATION
        else:
            entity_type = Entity.IRRELEVANT

        if entity_type != Entity.IRRELEVANT:
            entity_types[entity] = entity_type

    return entity_types
