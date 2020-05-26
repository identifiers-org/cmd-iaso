from urllib.parse import urlparse

from ..error import CurationError


def strip_scheme(url):
    parsed = urlparse(url)

    return parsed.geturl().replace("{}://".format(parsed.scheme), "", 1)


class SchemeRedirectError(CurationError):
    @staticmethod
    def check_and_create(provider):
        urls = set()

        for ping in provider.pings:
            for (rfrom, to) in zip(ping.redirects[:-1], ping.redirects[1:]):
                if strip_scheme(rfrom.url) == strip_scheme(to.url):
                    urls.add((rfrom.url, to.url))

        if len(urls) == 0:
            return True

        return SchemeRedirectError(urls)

    def __init__(self, urls):
        self.urls = urls

    def format(self, formatter):
        formatter.format_json(
            "Scheme Redirect",
            [f"<{url_from}> => <{url_to}>" for url_from, url_to in self.urls],
        )
