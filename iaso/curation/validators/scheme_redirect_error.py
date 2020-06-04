from urllib.parse import urlparse

from ..error import CurationError
from .collector import ErrorExampleCollector


def strip_scheme(url):
    parsed = urlparse(url)

    return parsed.geturl().replace("{}://".format(parsed.scheme), "", 1)


class SchemeRedirectError(CurationError):
    @staticmethod
    def check_and_create(
        get_compact_identifier, valid_luis_threshold, random_luis_threshold, provider
    ):
        collector = ErrorExampleCollector("Schema-Only Redirect")

        for ping in provider.pings:
            for (redirect_from, redirect_to) in zip(
                ping.redirects[:-1], ping.redirects[1:]
            ):
                collector.add(
                    f"{SchemeRedirectError.format_lui_link(redirect_from.url, ping.lui)} => {SchemeRedirectError.format_lui_link(redirect_to.url, ping.lui)}",
                    get_compact_identifier(ping.lui, provider.id),
                )

        if len(collector) == 0:
            return True

        return SchemeRedirectError(collector.result())

    def __init__(self, redirects):
        self.redirects = redirects

    def format(self, formatter):
        formatter.format_json("Scheme-Only Redirect", self.redirects, 2)
