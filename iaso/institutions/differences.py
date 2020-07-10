from collections import defaultdict
from enum import Enum, auto
from urllib.parse import urlparse

INSTITUTION_PROPERTIES = ["name", "homeUrl", "description", "rorId", "location"]


class Difference(Enum):
    MISSING = auto()
    ADD = auto()
    KEEP = auto()
    REPLACE = auto()
    SAME = auto()


def get_and_sanitise_prop(institution, prop):
    value = getattr(institution, prop)

    if value is None:
        return None

    if value == "CURATOR_REVIEW":
        return None

    return value


def strip_scheme(url):
    parsed = urlparse(url)

    return parsed.geturl().replace("{}://".format(parsed.scheme), "", 1)


def find_institution_differences(registry, academine):
    old_to_new_institution_entities = {
        institutions.id: set(institution.uuid for institution in institutions.entities)
        for institutions in academine.institutions
    }

    entity_resources = defaultdict(set)

    for rid, resource in registry.resources.items():
        for entity in old_to_new_institution_entities.get(resource.institution.id, []):
            entity_resources[entity].add(rid)

    institutions_differences = []

    for institutions in academine.institutions:
        old_institution = registry.institution.get(institutions.id)

        # Institution has been deleted or updated since collecting the ACADEMINE
        if old_institution is None or old_institution.name != institutions.string:
            continue

        institution_differences = []

        for new_institution in institutions.entities:
            institution_difference = {
                "matches": new_institution.matches,
                "occurrences": entity_resources[new_institution.uuid],
            }

            for prop in INSTITUTION_PROPERTIES:
                old_value = get_and_sanitise_prop(old_institution, prop)
                new_value = get_and_sanitise_prop(new_institution, prop)

                if old_value is None:
                    if new_value is None:
                        difference = {"type": Difference.MISSING}
                    else:
                        difference = {"type": Difference.ADD, "new": new_value}
                else:
                    if new_value is None:
                        difference = {"type": Difference.KEEP, "old": old_value}
                    elif str(new_value) != str(old_value):
                        if prop == "homeUrl" and strip_scheme(
                            old_value.rstrip("/")
                        ) == strip_scheme(new_value.rstrip("/")):
                            difference = Difference.KEEP
                        else:
                            difference = Difference.REPLACE

                        difference = {
                            "type": difference,
                            "new": new_value,
                            "old": old_value,
                        }
                    else:
                        difference = {
                            "type": Difference.SAME,
                            "same": old_value,
                        }

                institution_difference[prop] = difference

            institution_differences.append(institution_difference)

        # Keep original non-None description if 1-1 mapping between old and new institutions
        if (
            len(institution_differences) == 1
            and institution_differences[0]["description"]["type"] == Difference.REPLACE
        ):
            institution_differences[0]["description"]["type"] = Difference.KEEP

        institutions_differences.append(
            (
                institutions.id,
                {
                    "string": institutions.string,
                    "differences": institution_differences,
                },
            )
        )

    return institutions_differences
