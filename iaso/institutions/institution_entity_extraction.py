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
- parallelise extraction and linking
- add some visual output / interactive curation

"""


def query_wikidata_for_matching_entities(named_entities, wikidata_entity_matches=None):
    if wikidata_entity_matches is None:
        wikidata_entity_matches = defaultdict(set)

    for entity in named_entities:
        # Use the strict entity search based on labels and aliases
        with requests.get(
            f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={entity.lower()}&language=en&limit=10&props=&format=json"
        ) as req:
            for result in req.json()["search"]:
                wikidata_entity_matches[result["id"]].add(
                    (entity.lower(), result["match"]["text"].lower())
                )

        # Use the less strict search based on textual mentions
        with requests.get(
            f"https://www.wikidata.org/w/api.php?action=query&list=search&srsearch={entity.lower().replace(' ', ' OR ')}&srlimit=10&srprop=&format=json"
        ) as req:
            for result in req.json()["query"]["search"]:
                wikidata_entity_matches[result["title"]].add((entity.lower(), None))

    return wikidata_entity_matches


def filter_location_entities(wikidata_entities):
    query = (
        """
    SELECT DISTINCT ?location ?match WHERE {
      VALUES ?location { """
        + " ".join(f"wd:{qid}" for qid in wikidata_entities)
        + """ }
  
      ?location wdt:P31 ?class.
  
      FILTER EXISTS { ?class wdt:P279* wd:Q17334923 } # ?location is a location
      FILTER NOT EXISTS { ?class wdt:P279* wd:Q2385804 } # ?location is not an educational institution
      
      ?location rdfs:label ?match. FILTER (lang(?match) = "en").
    }
    """
    )

    with requests.get(
        "https://query.wikidata.org/sparql", params={"format": "json", "query": query}
    ) as req:
        location_entities = set()

        for result in req.json()["results"]["bindings"]:
            qid = result["location"]["value"][31:]

            location_entities.add(qid)

            wikidata_entities[qid] = set(
                (search, result["match"]["value"].lower() if match is None else match)
                for search, match in wikidata_entities[qid]
            )

    return location_entities


def filter_institution_entities(wikidata_entities):
    query = (
        """
    SELECT DISTINCT ?institution ?match WHERE {
      VALUES ?institution { """
        + " ".join(f"wd:{qid}" for qid in wikidata_entities)
        + """ }

      ?institution wdt:P31 ?class.
      
      FILTER EXISTS { ?class wdt:P279* wd:Q2385804 } # ?institution is an educational institution
      
      ?institution rdfs:label ?match. FILTER (lang(?match) = "en").
    }
    """
    )

    with requests.get(
        "https://query.wikidata.org/sparql", params={"format": "json", "query": query}
    ) as req:
        institution_entities = set()

        for result in req.json()["results"]["bindings"]:
            qid = result["institution"]["value"][31:]

            institution_entities.add(qid)

            wikidata_entities[qid] = set(
                (search, result["match"]["value"].lower() if match is None else match)
                for search, match in wikidata_entities[qid]
            )

    return institution_entities


def filter_institution_entities_with_match_scores(
    wikidata_entity_matches, institution_entities, location_entities
):
    candidate_institutions_with_match_scores = []

    for qid in institution_entities:
        terms = wikidata_entity_matches[qid]

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
            for aid, aterms in wikidata_entity_matches.items()
            for term in aterms
            if aid in location_entities and term[0] in searches and term[1] is not None
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

            # Filter out institutions where a location would be a better match
            if alternative_max_iou > term_max_iou[1]:
                continue

        if term_max_iou[1] > 0.0:
            candidate_institutions_with_match_scores.append(
                (
                    term_max_iou[0],
                    term_max_iou[1],
                    " ".join(WORD_PATTERN.split(term_max_iou[2])),
                )
            )

    return candidate_institutions_with_match_scores


def greedily_extract_institution_entities(institution_string):
    named_entity_monograms, named_entity_bigrams = extract_named_entities(
        institution_string
    )

    wikidata_entities = query_wikidata_for_matching_entities(named_entity_monograms)

    location_entities = filter_location_entities(wikidata_entities)

    location_matches = set(
        entity[0]
        for qid, entities in wikidata_entities.items()
        for entity in entities
        if qid in location_entities
    )

    # Find named entities which are followed by a location
    #  -> we should try out the bigram including the location as well to give more context
    #  -> but the context-including bigram should NOT generate any new entities, just eliminate some ambiguities
    for monogram, bigrams in zip(named_entity_monograms, named_entity_bigrams):
        extra_named_entities = set()

        for bigram in bigrams:
            if bigram.lower() in location_matches:
                extra_named_entities.add(f"{monogram} {bigram}")

        if len(extra_named_entities) == 0:
            continue

        monogram = monogram.lower()

        for qid, entities in wikidata_entities.items():
            extra_terms = []

            for search, match in entities:
                if search == monogram:
                    extra_terms.extend(
                        ((bigram.lower(), match) for bigram in extra_named_entities)
                    )

            wikidata_entities[qid].update(extra_terms)

    institution_entities = filter_institution_entities(wikidata_entities)

    candidate_institutions_with_match_scores = filter_institution_entities_with_match_scores(
        wikidata_entities, institution_entities, location_entities
    )

    # Sort by IoU score first, then by number of words matched
    candidate_institutions_with_match_scores.sort(
        key=lambda e: (e[1], e[2].count(" ")), reverse=True
    )

    institution_string = " ".join(WORD_PATTERN.split(institution_string.lower()))
    extracted_institution_entities = set()

    for qid, iou, search in candidate_institutions_with_match_scores:
        if search not in institution_string:
            continue

        institution_string = institution_string.replace(search, "")

        extracted_institution_entities.add(qid)

    return extracted_institution_entities
