from .named_entity_recognition import extract_named_entities
from .wikidataclient import RANKING_LIMIT

import asyncio
import re

from collections import Counter, defaultdict
from enum import Enum, auto

import httpx

WORD_PATTERN = re.compile(r"\W+")


class Entity(Enum):
    IRRELEVANT = auto()
    ORGANISATION = auto()
    LOCATION = auto()


async def greedily_extract_institution_entities(client, institution_string):
    named_entity_monograms, named_entity_bigrams = extract_named_entities(
        institution_string
    )

    named_entities = named_entity_monograms

    async def query_matching_entities(client, entity, wikidata_entity_matches):
        response = await client.search(entity)

        wikidata_entity_matches[entity.lower()] = [
            result["title"] for result in response["query"]["search"]
        ]

    wikidata_entity_matches = dict()

    await asyncio.gather(
        *[
            query_matching_entities(client, entity, wikidata_entity_matches)
            for entity in named_entities
        ]
    )

    restricted_qids = set(
        qid for qids in wikidata_entity_matches.values() for qid in qids
    )

    wikidata_entities = restricted_qids

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

        if is_organisation and not is_territorial_entity:
            entity_type = Entity.ORGANISATION
        elif is_location:
            entity_type = Entity.LOCATION
        else:
            entity_type = Entity.IRRELEVANT

        if entity_type != Entity.IRRELEVANT:
            entity_types[entity] = entity_type

    wikidata_entity_matches_no_locations = dict()
    wikidata_entity_only_locations = set()

    for match, qids in wikidata_entity_matches.items():
        qids = [
            qid
            for qid in qids
            if entity_types.get(qid, Entity.IRRELEVANT) != Entity.IRRELEVANT
        ]

        if len(qids) > 0 and entity_types[qids[0]] == Entity.LOCATION:
            wikidata_entity_only_locations.add(match)
        else:
            wikidata_entity_matches_no_locations[match] = {
                qid: i
                for i, qid in enumerate(qids)
                if entity_types[qid] == Entity.ORGANISATION
            }

    async def query_matching_bigram_entities(
        client, monogram, bigram, concensus_ranking
    ):
        response = await client.search(f"{monogram} {bigram}")

        ranking = {
            result["title"]: i for i, result in enumerate(response["query"]["search"])
        }

        for qid in wikidata_entity_matches_no_locations[monogram]:
            concensus_ranking[qid] += ranking.get(qid, RANKING_LIMIT)

    async def query_matching_monogram_entity(
        client,
        monogram,
        bigrams,
        wikidata_entity_only_locations,
        wikidata_entity_monogram_matches,
    ):
        monogram = monogram.lower()
        bigrams = [
            bigram.lower()
            for bigram in bigrams
            if bigram.lower() in wikidata_entity_only_locations
        ]

        if monogram in wikidata_entity_only_locations:
            return

        if len(bigrams) > 0:
            concensus_ranking = defaultdict(int)

            await asyncio.gather(
                *[
                    query_matching_bigram_entities(
                        client, monogram, bigram, concensus_ranking
                    )
                    for bigram in bigrams
                ]
            )

            ranking = {
                qid[0]: i
                for i, qid in enumerate(
                    sorted(concensus_ranking.items(), key=lambda e: e[1])
                )
            }
        else:
            ranking = wikidata_entity_matches_no_locations[monogram]

        query = (
            """SELECT DISTINCT ?institution WHERE {
          VALUES ?institution { """
            + " ".join(f"wd:{qid}" for qid in ranking)
            + """ }

          FILTER EXISTS {
            ?institution wdt:P31 ?class.
            ?class wdt:P279* wd:Q43229
          } # ?institution is an organisation
        }"""
        )

        response = await client.query(query)

        institution_entities = set(
            result["institution"]["value"][31:]
            for result in response["results"]["bindings"]
        )

        ranking = {qid: i for qid, i in ranking.items() if qid in institution_entities}

        if len(ranking) > 0:
            wikidata_entity_monogram_matches[monogram] = next(iter(ranking.items()))

    wikidata_entity_monogram_matches = dict()

    await asyncio.gather(
        *[
            query_matching_monogram_entity(
                client,
                monogram,
                bigrams,
                wikidata_entity_only_locations,
                wikidata_entity_monogram_matches,
            )
            for monogram, bigrams in zip(named_entity_monograms, named_entity_bigrams)
        ]
    )

    candidate_institutions_with_match_scores = [
        (search, qid, score)
        for search, (qid, score) in wikidata_entity_monogram_matches.items()
    ]

    candidate_institutions_with_match_scores.sort(
        key=lambda e: (-e[2], e[0].count(" "), len(e[0]), e[0]), reverse=True
    )

    consumed_institution_string = " ".join(
        WORD_PATTERN.split(institution_string.lower())
    )
    extracted_institution_entities = defaultdict(set)

    for search, qid, score in candidate_institutions_with_match_scores:
        if search not in consumed_institution_string:
            continue

        consumed_institution_string = consumed_institution_string.replace(search, "")

        extracted_institution_entities[qid].add(search)

    return extracted_institution_entities
