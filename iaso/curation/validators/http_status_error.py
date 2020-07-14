from collections import Counter

from requests import codes as status_code_values
from requests.status_codes import _codes as status_code_names

from ..validator import CurationValidator
from .collector import ErrorExampleCollector


class HTTPStatusError(CurationValidator):
    @staticmethod
    def check_and_create(
        get_compact_identifier, valid_luis_threshold, random_luis_threshold, provider
    ):
        status_codes = Counter(
            [
                ping.redirects[-1].status
                for ping in provider.pings
                if len(ping.redirects) > 0 and ping.redirects[-1].status is not None
            ]
        )

        if len(status_codes) == 0:
            return True

        total_valid_luis = len(
            [
                ping
                for ping in provider.pings
                if len(ping.redirects) > 0 and not ping.random
            ]
        )
        total_random_luis = len(
            [ping for ping in provider.pings if len(ping.redirects) > 0 and ping.random]
        )

        code_urls = dict()

        for status_code, frequency in status_codes.most_common():
            if status_code < status_code_values.multiple_choices:
                continue

            collector = ErrorExampleCollector("Final URL")

            error_valid_luis = len(
                [
                    ping
                    for ping in provider.pings
                    if len(ping.redirects) > 0
                    and ping.redirects[-1].status == status_code
                    and not ping.random
                ]
            )
            error_random_luis = len(
                [
                    ping
                    for ping in provider.pings
                    if len(ping.redirects) > 0
                    and ping.redirects[-1].status == status_code
                    and ping.random
                ]
            )

            include_valid_errors = (total_valid_luis > 0) and (
                (error_valid_luis / total_valid_luis) > valid_luis_threshold
            )
            include_random_errors = (total_random_luis > 0) and (
                (error_random_luis / total_random_luis) > random_luis_threshold
            )

            for ping in provider.pings:
                if (
                    len(ping.redirects) > 0
                    and ping.redirects[-1].status == status_code
                    and (
                        (ping.random and include_random_errors)
                        or (not ping.random and include_valid_errors)
                    )
                ):
                    collector.add(
                        HTTPStatusError.format_lui_link(
                            ping.redirects[-1].url, ping.lui
                        ),
                        get_compact_identifier(ping.lui, provider.id),
                    )

            if len(collector) > 0:
                code_urls[status_code] = collector.result()

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
                        for code in status_code_names.get(status_code, ["unknown"])
                        if "\\" not in code
                    ),
                ): urls
                for status_code, urls in self.code_urls.items()
            },
            3,
        )
