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
                if len(ping.redirects) > 0 and ping.redirects[-1].status is not None
            ]
        )

        if len(status_codes) == 0:
            return True

        code_urls = dict()

        for status_code, frequency in status_codes.most_common():
            if status_code < status_code_values.multiple_choices:
                continue

            code_urls[status_code] = [
                ping.redirects[0].url
                for ping in provider.pings
                if len(ping.redirects) > 0 and ping.redirects[-1].status == status_code
            ]

        if len(code_urls) == 0:
            return True

        return HTTPStatusError(code_urls)

    def __init__(self, code_urls):
        self.code_urls = code_urls

    def format(self, formatter):
        formatter.format_json(
            "Status code",
            {
                "{} ({})".format(
                    status_code,
                    ", ".join(
                        code.replace("_", " ")
                        for code in status_code_names.get(status_code, "unknown")
                        if "\\" not in code
                    ),
                ): [f"<{url}>" for url in urls]
                for status_code, urls in self.code_urls.items()
            },
        )
