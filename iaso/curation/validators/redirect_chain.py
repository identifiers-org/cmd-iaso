from ..validator import CurationValidator
from .collector import ErrorExampleCollector
from ..tag_store import TagStore

from requests import codes as status_code_values
from requests.status_codes import _codes as status_code_names


class RedirectChain(CurationValidator):
    @staticmethod
    def check_and_create(
        get_compact_identifier, valid_luis_threshold, random_luis_threshold, provider
    ):
        collector = ErrorExampleCollector("Redirection Chain")

        for ping in provider.pings:
            collector.add(
                [
                    {
                        "URL": RedirectChain.format_lui_link(redirect.url, ping.lui),
                        "HTTP Status": "{} ({})".format(
                            redirect.status,
                            ", ".join(
                                code.replace("_", " ")
                                for code in status_code_names.get(
                                    redirect.status, ["unknown"]
                                )
                                if "\\" not in code
                            ),
                        ),
                    }
                    for redirect in ping.redirects
                ],
                get_compact_identifier(ping.lui, provider.id),
                ping.random,
            )

        if len(collector) == 0:
            return True

        return RedirectChain(provider.id, collector.result())

    def __init__(self, rid, redirects):
        self.rid = rid
        self.redirects = redirects

    def format(self, formatter):
        formatter.format_json(
            RedirectChain.identify(self.rid), "Redirection Chain", self.redirects, 2
        )

    @staticmethod
    def identify(rid):
        return TagStore.serialise_identity(
            {
                "type": "RedirectChain",
                "rid": rid,
            }
        )
