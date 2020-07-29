from abc import ABC, abstractmethod


class CurationValidator(ABC):
    @staticmethod
    @abstractmethod
    def check_and_create(
        get_compact_identifier, valid_luis_threshold, random_luis_threshold, provider
    ):
        pass

    @staticmethod
    def format_lui_link(url, lui):
        return url.replace(lui, "{$id}") if lui in url else f"<{url}>"

    @abstractmethod
    def format(self, formatter):
        pass
