from ..recognition import extract_named_entities
from .substrings import fetch_wikidata_entities_matching_substrings
from .labels import fetch_wikidata_entity_labels
from .types import fetch_wikidata_entity_types
from .filter import filter_candidate_institutions
from .extraction import greedily_extract_institution_entities


async def greedily_match_institution_entities(client, institution_string):
    named_entity_nodes = extract_named_entities(institution_string)

    wikidata_entity_matches = await fetch_wikidata_entities_matching_substrings(
        client, named_entity_nodes
    )

    wikidata_entities = set(
        qid for hits, qids in wikidata_entity_matches.values() for qid in qids
    )

    wikidata_entity_labels = await fetch_wikidata_entity_labels(
        client, wikidata_entities
    )
    wikidata_entity_types = await fetch_wikidata_entity_types(client, wikidata_entities)

    candidate_institutions_with_match_hits = filter_candidate_institutions(
        wikidata_entity_matches, wikidata_entity_types, wikidata_entity_labels
    )

    extracted_institution_entities = greedily_extract_institution_entities(
        institution_string, candidate_institutions_with_match_hits
    )

    return extracted_institution_entities
