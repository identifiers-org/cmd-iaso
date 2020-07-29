import re

from itertools import chain

import spacy


def lazy_model_loader(model):
    def loader(*args, **kwargs):
        if loader.nlp is None:
            try:
                loader.nlp = spacy.load(model)
            except OSError:
                from spacy.cli import download

                download(model)

                loader.nlp = spacy.load(model)

        return loader.nlp(*args, **kwargs)

    loader.nlp = None

    return loader


nlp_en = lazy_model_loader("en_core_web_sm")
nlp_ml = lazy_model_loader("xx_ent_wiki_sm")

WORD_PATTERN = re.compile(r"\W+")


class NamedEntityNode:
    def __init__(self, text):
        self.__text = " ".join(WORD_PATTERN.split(text))
        self.__successors = set()

    def add(self, successor):
        self.__successors.add(successor)

    @property
    def text(self):
        return self.__text

    @property
    def successors(self):
        return self.__successors


def extract_named_entities(institution):
    doc_en = nlp_en(institution)
    doc_ml = nlp_ml(institution)

    named_entities = sorted(
        set((ent.text, ent.start, ent.end) for ent in chain(doc_en.ents, doc_ml.ents)),
        key=lambda e: e[1:],
    )

    nodes = tuple(NamedEntityNode(entity[0]) for entity in named_entities)

    for i, (entity, start, end) in enumerate(named_entities):
        n = i

        while n < len(named_entities) and named_entities[n][1] < end:
            n += 1

        if n < len(named_entities):
            next_start = named_entities[n][1]

            while n < len(named_entities) and named_entities[n][1] == next_start:
                nodes[i].add(nodes[n])

                n += 1

    return nodes
