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


def extract_named_entities(institution):
    doc_en = nlp_en(institution)
    doc_ml = nlp_ml(institution)

    named_entities = sorted(
        set((ent.text, ent.start, ent.end) for ent in chain(doc_en.ents, doc_ml.ents)),
        key=lambda e: e[1:],
    )

    monograms = tuple(entity[0] for entity in named_entities)

    bigrams = []

    for n, (entity, start, end) in enumerate(named_entities):
        successors = []

        while n < len(named_entities) and named_entities[n][1] < end:
            n += 1

        if n < len(named_entities):
            next_start = named_entities[n][1]

            while n < len(named_entities) and named_entities[n][1] == next_start:
                successors.append(named_entities[n][0])
                n += 1

        bigrams.append(tuple(successors))

    bigrams = tuple(bigrams)

    return (monograms, bigrams)
