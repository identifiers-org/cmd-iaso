from .differences import INSTITUTION_PROPERTIES, Difference

OK_DIFFERENCES = (Difference.KEEP, Difference.SAME)


def format_differences(difference, get_namespace_compact_identifier_link):
    difference = dict(difference)

    difference["occurences"] = [
        get_namespace_compact_identifier_link(rid) for rid in difference["occurences"]
    ]

    return difference


class InstitutionsValidator:
    @staticmethod
    def check_and_create(get_namespace_compact_identifier_link, entry):
        iid, differences = entry

        if all(
            institution[prop]["type"] in OK_DIFFERENCES
            for institution in differences["differences"]
            for prop in INSTITUTION_PROPERTIES
        ):
            return True

        return InstitutionsValidator(
            {
                "string": differences["string"],
                "differences": [
                    format_differences(
                        difference, get_namespace_compact_identifier_link
                    )
                    for difference in differences["differences"]
                ],
            }
        )

    def __init__(self, differences):
        self.differences = differences

    def format(self, formatter):
        formatter.format_json("Institution string", self.differences["string"], 1)

        if len(self.differences["differences"]) == 1:
            formatter.format_json(
                "Extracted institution", self.differences["differences"][0], 3,
            )
        else:
            formatter.format_json(
                f"Extracted institutions", self.differences["differences"], 3,
            )
