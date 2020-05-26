from abc import ABC, abstractmethod

from ..error import CurationError


class RedirectFlagError(CurationError, ABC):
    @staticmethod
    @abstractmethod
    def get_flag_from_redirect(redirect):
        pass

    @staticmethod
    def check_and_create(Subclass, provider):
        urls = set()

        for ping in provider.pings:
            for redirect in ping.redirects:
                if Subclass.get_flag_from_redirect(redirect) is True:
                    urls.add(redirect.url)

        if len(urls) == 0:
            return True

        return Subclass([f"<{url}>" for url in urls])

    def __init__(self, urls):
        self.urls = urls


class DNSError(RedirectFlagError):
    @staticmethod
    def get_flag_from_redirect(redirect):
        return redirect.dns_error

    @staticmethod
    def check_and_create(provider):
        return super(DNSError, DNSError).check_and_create(DNSError, provider)

    def format(self, formatter):
        formatter.format_json("DNS Error", self.urls)


class SSLError(RedirectFlagError):
    @staticmethod
    def get_flag_from_redirect(redirect):
        return redirect.ssl_error

    @staticmethod
    def check_and_create(provider):
        return super(SSLError, SSLError).check_and_create(SSLError, provider)

    def format(self, formatter):
        formatter.format_json("SSL Error", self.urls)


class InvalidResponseError(RedirectFlagError):
    @staticmethod
    def get_flag_from_redirect(redirect):
        return redirect.invalid_response

    @staticmethod
    def check_and_create(provider):
        return super(InvalidResponseError, InvalidResponseError).check_and_create(
            InvalidResponseError, provider
        )

    def format(self, formatter):
        formatter.format_json("Invalid Response", self.urls)
