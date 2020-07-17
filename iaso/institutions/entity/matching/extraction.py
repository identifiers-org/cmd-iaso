from collections import defaultdict

from ..recognition import WORD_PATTERN


def greedily_extract_institution_entities(
    institution_string, candidate_institutions_with_match_hits
):
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
