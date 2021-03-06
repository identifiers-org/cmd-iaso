from abc import ABC, abstractmethod
from collections import Counter

from ..tag_store import TagStore
from ..validator import CurationValidator
from .collector import ErrorExampleCollector


class RedirectFlagError(CurationValidator, ABC):
    @staticmethod
    @abstractmethod
    def get_flag_from_redirect(redirect):
        pass

    @staticmethod
    @abstractmethod
    def get_error_name():
        pass

    @staticmethod
    def check_and_create(
        get_compact_identifier,
        valid_luis_threshold,
        random_luis_threshold,
        Subclass,
        provider,
    ):
        collector = ErrorExampleCollector(Subclass.get_error_name())

        for ping in provider.pings:
            for redirect in ping.redirects:
                if Subclass.get_flag_from_redirect(redirect) is True:
                    collector.add(
                        RedirectFlagError.format_lui_link(redirect.url, ping.lui),
                        get_compact_identifier(ping.lui, provider.id),
                        ping.random,
                    )

        if len(collector) == 0:
            return True

        return Subclass(
            provider.id,
            collector.result(
                Counter(
                    get_compact_identifier(ping.lui, provider.id)
                    for ping in provider.pings
                )
            ),
        )

    def __init__(self, rid, urls):
        self.rid = rid
        self.urls = urls

    def format(self, formatter):
        formatter.format_json(
            RedirectFlagError.identify(type(self).__name__, self.rid),
            type(self).get_error_name(),
            self.urls,
            2,
        )

    @staticmethod
    def identify(type, rid):
        return TagStore.serialise_identity(
            {
                "type": type,
                "rid": rid,
            }
        )


class DNSError(RedirectFlagError):
    @staticmethod
    def get_flag_from_redirect(redirect):
        return redirect.dns_error

    @staticmethod
    def get_error_name():
        return "DNS Error"

    @staticmethod
    def check_and_create(
        get_compact_identifier, valid_luis_threshold, random_luis_threshold, provider
    ):
        return super(DNSError, DNSError).check_and_create(
            get_compact_identifier,
            valid_luis_threshold,
            random_luis_threshold,
            DNSError,
            provider,
        )


class SSLError(RedirectFlagError):
    @staticmethod
    def get_flag_from_redirect(redirect):
        return redirect.ssl_error

    @staticmethod
    def get_error_name():
        return "SSL Error"

    @staticmethod
    def check_and_create(
        get_compact_identifier, valid_luis_threshold, random_luis_threshold, provider
    ):
        return super(SSLError, SSLError).check_and_create(
            get_compact_identifier,
            valid_luis_threshold,
            random_luis_threshold,
            SSLError,
            provider,
        )


class InvalidResponseError(RedirectFlagError):
    @staticmethod
    def get_flag_from_redirect(redirect):
        return redirect.invalid_response

    @staticmethod
    def get_error_name():
        return "Invalid Response"

    @staticmethod
    def check_and_create(
        get_compact_identifier, valid_luis_threshold, random_luis_threshold, provider
    ):
        return super(InvalidResponseError, InvalidResponseError).check_and_create(
            get_compact_identifier,
            valid_luis_threshold,
            random_luis_threshold,
            InvalidResponseError,
            provider,
        )
