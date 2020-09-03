from abc import ABC, abstractmethod

import click


class CurationValidator(ABC):
    @classmethod
    def validate_params(cls, validator_name, **kwargs):
        """
        Overwrite this classmethod if your validator can take parameters.
        This method should either raise an exception or return a subclass of cls.
        """
        if len(kwargs) > 0:
            raise click.UsageError(
                click.style(
                    f"The validator {validator_name} does not accept any parameters.",
                    fg="red",
                )
            )

        return cls

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
