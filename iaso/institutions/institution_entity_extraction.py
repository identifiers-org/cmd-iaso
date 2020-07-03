import re

from collections import Counter, defaultdict

import requests

from .named_entity_recognition import extract_named_entities

HTML_TAG_PATTERN = re.compile(r"<.+?>")
WORD_PATTERN = re.compile(r"\W+")


"""

TODO:
- do not rely on title snippet in textual mentions, instead retrieve label for each entry and use that not strict match
- add graceful error handling if no JSON response
- ideally should not lose entire progress
- can we somehow integrate context ('Trinity College, Dublin' currently resolved to one of many Trinity Colleges as Dublin as a different entity)

"""


def query_wikidata_for_matching_entities(named_entities):
    wikidate_entity_matches = defaultdict(set)

    for entity in named_entities:
        # Use the strict entity search based on labels and aliases
        with requests.get(
            f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={entity.lower()}&language=en&limit=10&props=&format=json"
        ) as req:
            for result in req.json()["search"]:
                wikidate_entity_matches[result["id"]].add(
                    (entity.lower(), result["match"]["text"].lower())
                )

        # Use the less strict search based on textual mentions
        with requests.get(
            f"https://www.wikidata.org/w/api.php?action=query&list=search&srsearch={entity.lower().replace(' ', ' OR ')}&srlimit=10&srprop=titlesnippet&format=json"
        ) as req:
            for result in req.json()["query"]["search"]:
                wikidate_entity_matches[result["title"]].add(
                    (
                        entity.lower(),
                        HTML_TAG_PATTERN.sub("", result["titlesnippet"].lower()),
                    )
                )

    return wikidate_entity_matches


def filter_institution_and_location_entities(wikidata_entities):
    query = (
        """
    SELECT DISTINCT ?institution WHERE {
      VALUES ?institution {"""
        + " ".join(f"wd:{qid}" for qid in wikidata_entities)
        + """}

      ?institution wdt:P31 ?class. ?class wdt:P279+ wd:Q2385804. # ?institution is an educational institution
    }
    """
    )

    with requests.get(
        "https://query.wikidata.org/sparql", params={"format": "json", "query": query}
    ) as req:
        institution_entities = set(
            result["institution"]["value"][31:]
            for result in req.json()["results"]["bindings"]
        )

    query = (
        """
    SELECT DISTINCT ?location WHERE {
      VALUES ?location {"""
        + " ".join(f"wd:{qid}" for qid in wikidata_entities)
        + """}

      ?location wdt:P31 ?class. ?class wdt:P279+ wd:Q17334923. # ?location is a location
    }
    """
    )

    with requests.get(
        "https://query.wikidata.org/sparql", params={"format": "json", "query": query}
    ) as req:
        location_entities = set(
            result["location"]["value"][31:]
            for result in req.json()["results"]["bindings"]
        ).difference(institution_entities)

    return (institution_entities, location_entities)


def filter_institution_entities_with_match_scores(wikidate_entity_matches):
    institution_entities, location_entities = filter_institution_and_location_entities(
        wikidate_entity_matches
    )

    candidate_institutions_with_match_scores = []

    for qid in institution_entities:
        terms = wikidate_entity_matches[qid]

        term_ious = []

        for search, match in terms:
            search_set = Counter(s for s in WORD_PATTERN.split(search) if len(s) > 0)
            match_set = Counter(m for m in WORD_PATTERN.split(match) if len(m) > 0)

            iou = len(search_set & match_set) / len(search_set | match_set)

            term_ious.append((qid, iou, search, match))

        term_max_iou = max(
            (term_iou[:-1] for term_iou in term_ious), key=lambda e: e[1]
        )

        searches, matches = zip(*terms)
        alternatives = set(
            (aid, term[0], term[1])
            for aid, aterms in wikidate_entity_matches.items()
            for term in aterms
            if aid in location_entities and term[0] in searches
        )

        if len(alternatives) > 0:
            alternative_ious = []

            for aid, search, match in alternatives:
                search_set = Counter(
                    s for s in WORD_PATTERN.split(search) if len(s) > 0
                )
                match_set = Counter(m for m in WORD_PATTERN.split(match) if len(m) > 0)

                iou = len(search_set & match_set) / len(search_set | match_set)

                alternative_ious.append((aid, iou, search, match))

            alternative_max_iou = max(
                alternative_iou[1] for alternative_iou in alternative_ious
            )

            if alternative_max_iou > term_max_iou[1]:
                continue

        candidate_institutions_with_match_scores.append(term_max_iou)

    return candidate_institutions_with_match_scores


def greedily_extract_institution_entities(institution_string):
    candidate_institutions_with_match_scores = filter_institution_entities_with_match_scores(
        query_wikidata_for_matching_entities(extract_named_entities(institution_string))
    )

    candidate_institutions_with_match_scores.sort(key=lambda e: e[1], reverse=True)

    institution_string = institution_string.lower()
    extracted_institution_entities = set()

    for qid, iou, search in candidate_institutions_with_match_scores:
        if search not in institution_string:
            continue

        institution_string = institution_string.replace(search, "")

        extracted_institution_entities.add(qid)

    return extracted_institution_entities
