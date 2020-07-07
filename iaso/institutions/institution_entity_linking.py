import requests

from pycountry import countries


def get_optional_sparql_field(result, field, func=None):
    value = result.get(field)

    if value is None:
        return None

    value = value["value"]

    if func is None:
        return value

    return func(value)


async def query_institution_entity_details(client, institution_entities):
    institution_entity_details = dict()

    query = (
        """
    SELECT ?institution ?name ?description ?homeUrl ?rorId ?location WHERE {
      SERVICE <http://dbpedia.org/sparql> {
        VALUES ?institution { """
        + " ".join(f"wd:{qid}" for qid in institution_entities)
        + """ }

        OPTIONAL { ?institution rdfs:label ?name. FILTER (lang(?name) = "en") }

        OPTIONAL {
          ?dbpedia_id owl:sameAs ?institution.
          ?dbpedia_id rdfs:comment ?description. FILTER (lang(?description) = "en")
        }
      }

      OPTIONAL { ?institution wdt:P856 ?homeUrl }
      OPTIONAL { ?institution wdt:P6782 ?rorId }
      OPTIONAL { ?institution wdt:P17 ?country. ?country wdt:P297 ?location }
    }
    """
    )

    response = await client.query(query)

    for result in response["results"]["bindings"]:
        institution_entity_details[result["institution"]["value"][31:]] = {
            "name": get_optional_sparql_field(result, "name"),
            "homeUrl": get_optional_sparql_field(result, "homeUrl"),
            "description": get_optional_sparql_field(result, "description"),
            "rorId": get_optional_sparql_field(
                result, "rorId", lambda rorId: f"https://ror.org/{rorId}"
            ),
            "location": get_optional_sparql_field(
                result,
                "location",
                lambda location: {
                    "countryCode": location,
                    "countryName": countries.get(alpha_2=location).name,
                },
            ),
        }

    return institution_entity_details
