async def fetch_wikidata_entity_labels(client, wikidata_entities):
    query = (
        """SELECT DISTINCT ?entity ?label WHERE {
      VALUES ?entity { """
        + " ".join(f"wd:{qid}" for qid in wikidata_entities)
        + """ }

      ?entity rdfs:label ?label. FILTER (lang(?label) = "en").
    }"""
    )

    response = await client.query(query)

    entity_labels = dict()

    for result in response["results"]["bindings"]:
        entity_labels[result["entity"]["value"][31:]] = result["label"]["value"]

    return entity_labels
