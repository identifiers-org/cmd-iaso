from ..error import CurationError
from .collector import ErrorExampleCollector

from requests import codes as status_code_values
from requests.status_codes import _codes as status_code_names


class RedirectChain(CurationError):
    @staticmethod
    def check_and_create(get_compact_identifier, provider):
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
            )

        if len(collector) == 0:
            return True

        return RedirectChain(collector.result())

    def __init__(self, redirects):
        self.redirects = redirects

    def format(self, formatter):
        formatter.format_json("Redirection Chain", self.redirects, 2)
