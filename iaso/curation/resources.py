from functools import partial

import click

from ..format_json import format_json
from . import curate
from .validators.http_status_error import HTTPStatusError
from .validators.redirect_chain import RedirectChain
from .validators.redirect_flag_error import DNSError, InvalidResponseError, SSLError
from .validators.scheme_redirect_error import SchemeRedirectError


def get_curation_data_and_validators_resources(session, registry, provider_namespace):
    click.echo(
        click.style(
            "The data loaded was collected in the following environment:", fg="yellow"
        )
    )
    click.echo(format_json(session.datamine.environment))

    validator_names = list(
        validator_string.split(":", 1)[0]
        for validator_string in session.validators.keys()
    )

    if len(validator_names) == 0:
        click.echo(click.style("No validators were loaded.", fg="red"))
    elif len(validator_names) == 1:
        click.echo(
            click.style(f"The {validator_names[0]} validator was loaded.", fg="yellow")
        )
    else:
        click.echo(
            click.style(
                "The {} and {} validators were loaded.".format(
                    ", ".join(validator_names[:-1]), validator_names[-1]
                ),
                fg="yellow",
            )
        )

    def get_compact_identifier(lui, pid):
        if provider_namespace[pid].namespaceEmbeddedInLui:
            return lui

        return f"{provider_namespace[pid].prefix}:{lui}"

    return (
        session.datamine.providers,
        [
            lambda p: p.id in registry.resources,
            *[
                partial(
                    validator.check_and_create,
                    get_compact_identifier,
                    session.valid_luis_threshold / 100,
                    session.random_luis_threshold / 100,
                )
                for validator in session.validators.values()
            ],
        ],
    )


def get_navigation_url_auxiliary_resources(entry, registry, provider_namespace):
    namespace = provider_namespace[entry.entry.id]
    provider = registry.resources[entry.entry.id]

    navigation_url = "https://registry.identifiers.org/registry/{}".format(
        namespace.prefix
    )

    return (navigation_url, provider.urlPattern)


def get_informant_title_description_resources(entry, registry, provider_namespace):
    provider = registry.resources[entry.entry.id]

    return (
        {"type": "resource provider", "text": provider.name},
        "The following issues were observed:",
    )


async def curate_resources(
    registry,
    Controller,
    Navigator,
    Informant,
    tag_store,
    session,
):
    await curate(
        registry,
        Controller,
        Navigator,
        Informant,
        tag_store,
        session,
        get_curation_data_and_validators_resources,
        get_navigation_url_auxiliary_resources,
        get_informant_title_description_resources,
    )
