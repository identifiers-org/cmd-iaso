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

        return [SchemeRedirectError(*url) for url in urls]

    def __init__(self, url_from, url_to):
        self.url_from = url_from
        self.url_to = url_to

    def format(self, formatter):
        formatter.format_json(
            "Scheme Redirect", "{} => {}".format(self.url_from, self.url_to),
        )
