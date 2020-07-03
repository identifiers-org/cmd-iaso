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

    return set(ent.text for ent in chain(doc_en.ents, doc_ml.ents))
