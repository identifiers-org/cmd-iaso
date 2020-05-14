from collections import Counter

from requests.status_codes import _codes as status_codes

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

        # TODO: redirects should also not be allowed here
        if status_code < 400:
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
                    for code in status_codes.get(self.status_code, "unknown")
                    if "\\" not in code
                ),
            ),
        )
        formatter.format_json(
            "Test JSON Data",
            {
                "hello": [1, 2, 3, 4],
                "bye": [4, 3, 2, 1],
                "there": {
                    "a": 1,
                    "b": 2,
                    "c": ["hello", None],
                    "there": {"a": 1, "b": 2, "c": ["hello", None]},
                },
            },
        )
