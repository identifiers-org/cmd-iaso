from itertools import chain

import spacy

nlp_en = spacy.load("en_core_web_sm")
nlp_ml = spacy.load("xx_ent_wiki_sm")


def extract_named_entities(institution):
    doc_en = nlp_en(institution)
    doc_ml = nlp_ml(institution)

    return set(ent.text for ent in chain(doc_en.ents, doc_ml.ents))
