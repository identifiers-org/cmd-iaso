from collections import Counter

from requests import codes as status_code_values
from requests.status_codes import _codes as status_code_names

from ..error import CurationError


class HTTPStatusError(CurationError):
    @staticmethod
    def check_and_create(provider):
        status_codes = Counter(
            [
                ping.redirects[-1].status
                for ping in provider.pings
                if len(ping.redirects) > 0
            ]
        )

        if len(status_codes) == 0:
            return True

        status_code, frequency = status_codes.most_common(1)[0]

        if status_code < status_code_values.multiple_choices:
            return True

        return HTTPStatusError(status_code)

    def __init__(self, status_code):
        self.status_code = status_code

    def format(self, formatter):
        formatter.format_json(
            "Status code",
            "{} ({})".format(
                self.status_code,
                ", ".join(
                    code.replace("_", " ")
                    for code in status_code_names.get(self.status_code, "unknown")
                    if "\\" not in code
                ),
            ),
        )
