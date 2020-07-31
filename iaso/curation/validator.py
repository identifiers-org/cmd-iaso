from abc import ABC, abstractmethod


class CurationValidator(ABC):
    @staticmethod
    @abstractmethod
    def check_and_create(
        get_compact_identifier, valid_luis_threshold, random_luis_threshold, provider
    ):
        """
        Returns False iff this data_entry cannot be included during
         curation at all.
        Returns True iff this validator has found nothing to report on
         this data_entry.
        Returns an instance of the particular CurationValidator iff it
         found something to report about this data_entry.
        """
        pass

    @staticmethod
    def format_lui_link(url, lui):
        return url.replace(lui, "{$id}") if lui in url else f"<{url}>"

    @abstractmethod
    def format(self, formatter):
        pass
