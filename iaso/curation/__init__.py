from functools import partial

from ..utils import format_json

from .validators.redirect_chain import RedirectChain
from .validators.http_status_error import HTTPStatusError
from .validators.redirect_flag_error import DNSError, SSLError, InvalidResponseError
from .validators.scheme_redirect_error import SchemeRedirectError

from .interact import CurationController, CurationNavigator, CurationFormatter
from .generator import curation_entry_generator, CurationDirection

import click


async def curate(
    registry, datamine, Controller, Navigator, Informant, show_redirect_chain
):
    click.echo("The data loaded was collected in the following environment:")
    click.echo(format_json(datamine.environment))

    provider_namespace = dict()

    for nid, namespace in registry.namespaces.items():
        for resource in namespace.resources:
            provider_namespace[resource.id] = namespace

    def get_compact_identifier(lui, pid):
        if provider_namespace[pid].namespaceEmbeddedInLui:
            return lui

        return f"{provider_namespace[pid].prefix}:{lui}"

    validators = [
        DNSError,
        SSLError,
        InvalidResponseError,
        HTTPStatusError,
        SchemeRedirectError,
    ]

    if show_redirect_chain:
        validators.insert(0, RedirectChain)

    entries = curation_entry_generator(
        datamine.providers,
        [
            lambda p: p.id in registry.resources,
            *[
                partial(validator.check_and_create, get_compact_identifier)
                for validator in validators
            ],
        ],
    )

    click.echo(click.style("Starting the curation process ...", fg="yellow"))

    next(entries)
    entry = entries.send(CurationDirection.FORWARD)

    if entry == CurationDirection.FINISH:
        click.echo(
            click.style("There are no entries that require curation.", fg="green")
        )
    else:
        async with await CurationController.create(
            Controller
        ) as controller, await CurationNavigator.create(
            Navigator
        ) as navigator, await CurationFormatter.create(
            Informant
        ) as informant:
            while entry != CurationDirection.FINISH:
                for validation in entry.validations:
                    validation.format(informant)

                namespace = provider_namespace[entry.entry.id]
                provider = registry.resources[entry.entry.id]

                navigation_url = "https://registry.identifiers.org/registry/{}".format(
                    namespace.prefix
                )

                await navigator.navigate(navigation_url, provider.urlPattern)

                await informant.output(
                    navigation_url, provider, namespace, entry.position, entry.total
                )

                next(entries)

                entry = entries.send(await controller.prompt())

    click.echo(click.style("Finishing the curation process ...", fg="yellow"))
