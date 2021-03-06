from collections import Counter
from urllib.parse import urlparse

from ..tag_store import TagStore
from ..validator import CurationValidator
from .collector import ErrorExampleCollector


def strip_scheme(url):
    parsed = urlparse(url)

    return parsed.geturl().replace("{}://".format(parsed.scheme), "", 1)


class SchemeRedirectError(CurationValidator):
    @staticmethod
    def check_and_create(
        get_compact_identifier, valid_luis_threshold, random_luis_threshold, provider
    ):
        collector = ErrorExampleCollector("Schema-Only Redirect")

        for ping in provider.pings:
            for (redirect_from, redirect_to) in zip(
                ping.redirects[:-1], ping.redirects[1:]
            ):
                if (redirect_from.url != redirect_to.url) and (
                    strip_scheme(redirect_from.url) == strip_scheme(redirect_to.url)
                ):
                    collector.add(
                        f"{SchemeRedirectError.format_lui_link(redirect_from.url, ping.lui)} => "
                        + f"{SchemeRedirectError.format_lui_link(redirect_to.url, ping.lui)}",
                        get_compact_identifier(ping.lui, provider.id),
                        ping.random,
                    )

        if len(collector) == 0:
            return True

        return SchemeRedirectError(
            provider.id,
            collector.result(
                Counter(
                    get_compact_identifier(ping.lui, provider.id)
                    for ping in provider.pings
                )
            ),
        )

    def __init__(self, rid, redirects):
        self.rid = rid
        self.redirects = redirects

    def format(self, formatter):
        formatter.format_json(
            SchemeRedirectError.identify(
                self.rid,
                [redirect["Schema-Only Redirect"] for redirect in self.redirects],
            ),
            "Scheme-Only Redirect",
            self.redirects,
            2,
        )

    @staticmethod
    def identify(rid, redirects):
        return TagStore.serialise_identity(
            {
                "type": "SchemaRedirectError",
                "rid": rid,
                "redirects": sorted(redirects),
            }
        )
