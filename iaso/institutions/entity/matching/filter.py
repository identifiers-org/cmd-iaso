from collections import Counter

from ..recognition import WORD_PATTERN
from .types import Entity


def filter_candidate_institutions(
    wikidata_entity_matches, wikidata_entity_types, wikidata_entity_labels
):
    candidate_institutions_with_match_hits = []

    for match, (hits, qids) in wikidata_entity_matches.items():
        qids = [
            qid
            for qid in qids
            if wikidata_entity_types.get(qid, Entity.IRRELEVANT) != Entity.IRRELEVANT
        ]

        normalised_match = Counter(WORD_PATTERN.split(match.lower()))

        qid_ious = []

        for qid in qids:
            normalised_label = Counter(
                WORD_PATTERN.split(wikidata_entity_labels.get(qid, "").lower())
            )

            qid_ious.append(
                (
                    qid,
                    len(normalised_match & normalised_label)
                    / len(normalised_match | normalised_label),
                )
            )

        qid_ious.sort(key=lambda e: e[1], reverse=True)

        if len(qids) > 0 and wikidata_entity_types[qid_ious[0][0]] != Entity.LOCATION:
            candidate_institutions_with_match_hits.append(
                (
                    match,
                    set(
                        qid
                        for qid in qids
                        if wikidata_entity_types[qid] == Entity.ORGANISATION
                    ),
                    hits,
                )
            )

    return candidate_institutions_with_match_hits
