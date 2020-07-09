from enum import Enum, auto

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


def find_institution_differences(registry, academine):
    institutions_differences = []

    for institutions in academine.institutions:
        old_institution = registry.institution.get(institutions.id)

        # Institution has been deleted or updated since collecting the ACADEMINE
        if old_institution is None or old_institution.name != institutions.string:
            continue

        institution_differences = []

        for new_institution in institutions.entities:
            institution_difference = {"matches": new_institution.matches}

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
                        difference = {
                            "type": Difference.REPLACE,
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
