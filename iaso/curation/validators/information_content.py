from collections import Counter

import click

from requests import codes as status_code_values

from ..validator import CurationValidator
from .collector import ErrorExampleCollector
from ..tag_store import TagStore


class InformationContent(CurationValidator):
    @classmethod
    def validate_params(cls, validator_name, **kwargs):
        threshold = kwargs.pop("threshold", 0.1)

        try:
            if threshold is True:
                raise Exception

            threshold = float(threshold)

            if threshold < 0.0 or threshold > 1.0:
                raise Exception
        except Exception as err:
            raise click.UsageError(
                click.style(
                    f"The validator {validator_name} has been parameterised "
                    + f"with an invalid threshold: {threshold}. The threshold "
                    + "should be in range [0.0, 1.0].",
                    fg="red",
                )
            )

        if len(kwargs) > 0:
            params = list(kwargs.keys())

            if len(params) == 1:
                params = f"'{params[0]}'"
            else:
                params = " and ".join(
                    (
                        ", ".join(f"'{param}'" for param in params[:-1]),
                        f"'{params[-1]}'",
                    )
                )

            raise click.UsageError(
                click.style(
                    f"Validator {validator_name} has been provided with the "
                    + f"following extraneous parameter"
                    + f"{'' if len(params) == 1 else 's'}: {params}. "
                    + "It only supports the 'threshold' parameter.",
                    fg="red",
                )
            )

        class InformationContentWithThreshold(InformationContent):
            @staticmethod
            def check_and_create(*args):
                return InformationContent.check_and_create(threshold, *args)

        return InformationContentWithThreshold

    @staticmethod
    def check_and_create(
        threshold,
        get_compact_identifier,
        valid_luis_threshold,
        random_luis_threshold,
        provider,
    ):
        if provider.analysis is None:
            return True

        total_information_content = max(
            (item.information_content for item in provider.analysis), default=None
        )

        if total_information_content is None or total_information_content > threshold:
            return True

        collector = ErrorExampleCollector("Resource Information Content")

        total_information_content_title = "{:.1%}".format(total_information_content)

        analysis_per_compid = {
            get_compact_identifier(item.lui, provider.id): item
            for item in provider.analysis
        }

        for ping in provider.pings:
            if (
                ping.empty_content is False
                and len(ping.redirects) > 0
                and ping.redirects[-1].status == status_code_values.ok
            ):
                collector.add(
                    total_information_content_title,
                    get_compact_identifier(ping.lui, provider.id),
                    ping.random,
                )

        if len(collector) == 0:
            return True

        assert len(collector) == 1

        information_content = collector.result_compid_dict(
            Counter(
                get_compact_identifier(ping.lui, provider.id) for ping in provider.pings
            )
        )[0]

        information_content["Example Compact Identifiers"] = [
            {
                "Compact Identifier": compid_string,
                "Information Content": "{:.1%}".format(
                    analysis_per_compid[compid].information_content
                ),
                "Common Content Length": f"{analysis_per_compid[compid].length} words",
                "Number of NOISE segments": analysis_per_compid[compid].noise,
            }
            for compid_string, compid in sorted(
                information_content["Example Compact Identifiers"].items(),
                key=lambda kv: analysis_per_compid[kv[1]].information_content,
                reverse=True,
            )
        ]

        return InformationContent(
            provider.id, information_content, total_information_content
        )

    def __init__(self, rid, information_content, total_information_content):
        self.rid = rid
        self.information_content = information_content
        self.total_information_content = total_information_content

    def format(self, formatter):
        formatter.format_json(
            InformationContent.identify(
                self.rid,
                self.total_information_content,
            ),
            "Information Content",
            self.information_content,
            1,
        )

    @staticmethod
    def identify(rid, total_information_content):
        return TagStore.serialise_identity(
            {
                "type": "InformationContent",
                "rid": rid,
                "total_information_content": round(total_information_content, 1),
            }
        )
