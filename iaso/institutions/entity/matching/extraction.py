from collections import Counter, defaultdict

from ..recognition import WORD_PATTERN


def greedily_extract_institution_entities(
    institution_string, candidate_institutions_with_match_hits
):
    candidate_institutions_with_match_hits.sort(
        key=lambda e: (-e[2], e[0].count(" "), len(e[0]), e[0]), reverse=True
    )

    consumed_institution_words = Counter(WORD_PATTERN.split(institution_string.lower()))

    extracted_institution_entities = defaultdict(set)

    for search, qids, hits in candidate_institutions_with_match_hits:
        search_words = Counter(WORD_PATTERN.split(search))

        if (consumed_institution_words & search_words) != search_words:
            continue

        consumed_institution_words -= search_words

        for qid in qids:
            extracted_institution_entities[qid].add(search)

    return extracted_institution_entities
