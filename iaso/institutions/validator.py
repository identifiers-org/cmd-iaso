import json

from copy import deepcopy

from .differences import INSTITUTION_PROPERTIES, Difference

OK_DIFFERENCES = (Difference.KEEP, Difference.SAME)
URL_PROPERTIES = ["homeUrl", "rorId"]


def format_differences(difference, get_namespace_compact_identifier_link):
    difference = deepcopy(difference)

    difference["occurrences"] = [
        get_namespace_compact_identifier_link(rid) for rid in difference["occurrences"]
    ]

    for prop in INSTITUTION_PROPERTIES:
        difference[prop]["type"] = str(difference[prop]["type"])

        if prop in URL_PROPERTIES:
            for subprop, value in difference[prop].items():
                if subprop == "type":
                    continue

                if value is not None:
                    difference[prop][subprop] = f"<{value}>"

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
            iid,
            {
                "string": differences["string"],
                "differences": [
                    format_differences(
                        difference, get_namespace_compact_identifier_link
                    )
                    for difference in differences["differences"]
                ],
            },
        )

    def __init__(self, iid, differences):
        self.iid = iid
        self.differences = differences

    def format(self, formatter):
        for difference in self.differences["differences"]:
            formatter.format_json(
                InstitutionsValidator.identify(
                    self.iid, self.differences["string"], difference
                ),
                difference["name"].get("same")
                or difference["name"].get("new")
                or difference["name"]["old"],
                difference,
                3,
            )

    @staticmethod
    def identify(iid, string, difference):
        return json.dumps(
            {
                "iid": iid,
                "string": string,
                "difference": {
                    k: v
                    for k, v in difference.items()
                    if k not in ["matches", "occurrences"]
                },
            },
            separators=(",", ":"),
            sort_keys=True,
        )
