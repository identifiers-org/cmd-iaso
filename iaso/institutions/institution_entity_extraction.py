import asyncio

from collections import Counter, defaultdict
from enum import Enum, auto

from .named_entity_recognition import extract_named_entities, WORD_PATTERN
from .wikidataclient import RANKING_LIMIT


class Entity(Enum):
    IRRELEVANT = auto()
    ORGANISATION = auto()
    LOCATION = auto()


async def greedily_extract_institution_entities(client, institution_string):
    named_entity_nodes = extract_named_entities(institution_string)

    async def query_matching_entities(client, entity, strict, wikidata_entity_matches):
        response = await client.search(entity, strict=strict)

        hits = response["query"]["searchinfo"]["totalhits"]
        qids = [result["title"] for result in response["query"]["search"]]

        wikidata_entity_matches[entity.lower()] = (hits, qids)

    wikidata_node_matches = dict()

    await asyncio.gather(
        *[
            query_matching_entities(client, text, True, wikidata_node_matches)
            for text in set(node.text for node in named_entity_nodes)
        ]
    )

    queue = [("", node) for node in named_entity_nodes]

    queries = []

    wikidata_entity_matches = dict()

    while len(queue) > 0:
        prefix, node = queue.pop(0)

        matched_hits, matched_qids = wikidata_node_matches[node.text.lower()]

        if len(matched_qids) == 0:
            if len(prefix) == 0:
                queries.append((node.text, False))

            continue

        if len(prefix) == 0:
            wikidata_entity_matches[node.text.lower()] = (matched_hits, matched_qids)
        else:
            queries.append((f"{prefix} {node.text}", True))

        for successor in node.successors:
            queue.append((f"{prefix} {node.text}", successor))

    await asyncio.gather(
        *[
            query_matching_entities(client, text, strict, wikidata_entity_matches)
            for text, strict in queries
        ]
    )

    restricted_qids = set(
        qid for hits, qids in wikidata_entity_matches.values() for qid in qids
    )

    wikidata_entities = restricted_qids

    query = (
        """SELECT DISTINCT ?entity ?label WHERE {
      VALUES ?entity { """
        + " ".join(f"wd:{qid}" for qid in wikidata_entities)
        + """ }

      ?entity rdfs:label ?label. FILTER (lang(?label) = "en").
    }"""
    )

    response = await client.query(query)

    entity_labels = dict()

    for result in response["results"]["bindings"]:
        entity_labels[result["entity"]["value"][31:]] = result["label"]["value"]

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

    candidate_institutions_with_match_hits = []

    for match, (hits, qids) in wikidata_entity_matches.items():
        qids = [
            qid
            for qid in qids
            if entity_types.get(qid, Entity.IRRELEVANT) != Entity.IRRELEVANT
        ]

        normalised_match = Counter(WORD_PATTERN.split(match.lower()))

        qid_ious = []

        for qid in qids:
            normalised_label = Counter(
                WORD_PATTERN.split(entity_labels.get(qid, "").lower())
            )

            qid_ious.append(
                (
                    qid,
                    len(normalised_match & normalised_label)
                    / len(normalised_match | normalised_label),
                )
            )

        qid_ious.sort(key=lambda e: e[1], reverse=True)

        if len(qids) > 0 and entity_types[qid_ious[0][0]] != Entity.LOCATION:
            candidate_institutions_with_match_hits.append(
                (
                    match,
                    set(
                        qid for qid in qids if entity_types[qid] == Entity.ORGANISATION
                    ),
                    hits,
                )
            )

    candidate_institutions_with_match_hits.sort(
        key=lambda e: (-e[2], e[0].count(" "), len(e[0]), e[0]), reverse=True
    )

    consumed_institution_string = " ".join(
        WORD_PATTERN.split(institution_string.lower())
    )
    extracted_institution_entities = defaultdict(set)

    for search, qids, hits in candidate_institutions_with_match_hits:
        if search not in consumed_institution_string:
            continue

        consumed_institution_string = consumed_institution_string.replace(search, "")

        for qid in qids:
            extracted_institution_entities[qid].add(search)

    return extracted_institution_entities
