import asyncio


async def query_matching_entities(client, entity, strict, wikidata_entity_matches):
    response = await client.search(entity, strict=strict)

    hits = response["query"]["searchinfo"]["totalhits"]
    qids = [result["title"] for result in response["query"]["search"]]

    wikidata_entity_matches[entity.lower()] = (hits, qids)


async def fetch_wikidata_entities_matching_substrings(client, named_entity_nodes):
    wikidata_node_matches = dict()

    await asyncio.gather(
        *[
            query_matching_entities(client, text, True, wikidata_node_matches)
            for text in set(node.text for node in named_entity_nodes)
        ]
    )

    queue = [("", node) for node in named_entity_nodes]

    queries = []

    wikidata_entity_matches = dict()

    while len(queue) > 0:
        prefix, node = queue.pop(0)

        matched_hits, matched_qids = wikidata_node_matches[node.text.lower()]

        if len(matched_qids) == 0:
            if len(prefix) == 0:
                queries.append((node.text, False))

            continue

        if len(prefix) == 0:
            wikidata_entity_matches[node.text.lower()] = (matched_hits, matched_qids)
        else:
            queries.append((f"{prefix} {node.text}", True))

        for successor in node.successors:
            queue.append((f"{prefix} {node.text}", successor))

    await asyncio.gather(
        *[
            query_matching_entities(client, text, strict, wikidata_entity_matches)
            for text, strict in queries
        ]
    )

    return wikidata_entity_matches
