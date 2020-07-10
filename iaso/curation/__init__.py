from collections import defaultdict
from functools import partial

from ..utils import format_json

from .validators.redirect_chain import RedirectChain
from .validators.http_status_error import HTTPStatusError
from .validators.redirect_flag_error import DNSError, SSLError, InvalidResponseError
from .validators.scheme_redirect_error import SchemeRedirectError

from .interact import CurationController, CurationNavigator, CurationFormatter
from .generator import curation_entry_generator, CurationDirection

from ..institutions.differences import find_institution_differences
from ..institutions.validator import InstitutionsValidator

import click


async def curate_resources(
    registry, Controller, Navigator, Informant, session,
):
    click.echo(
        click.style(
            "The data loaded was collected in the following environment:", fg="yellow"
        )
    )
    click.echo(format_json(session.datamine.environment))

    provider_namespace = dict()

    for nid, namespace in registry.namespaces.items():
        for resource in namespace.resources:
            provider_namespace[resource.id] = namespace

    def get_compact_identifier(lui, pid):
        if provider_namespace[pid].namespaceEmbeddedInLui:
            return lui

        return f"{provider_namespace[pid].prefix}:{lui}"

    entries = curation_entry_generator(
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

    next(entries)
    entries.send(session.position)

    validator_names = list(session.validators.keys())

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

    click.echo(click.style("Starting the curation process ...", fg="yellow"))

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
                session.update(entry.index, entry.visited)

                for validation in entry.validations:
                    validation.format(informant)

                namespace = provider_namespace[entry.entry.id]
                provider = registry.resources[entry.entry.id]

                navigation_url = "https://registry.identifiers.org/registry/{}".format(
                    namespace.prefix
                )

                await navigator.navigate(navigation_url, provider.urlPattern)

                await informant.output(
                    navigation_url,
                    {"type": "resource provider", "text": provider.name,},
                    "The following issues were observed:",
                    entry.position,
                    entry.total,
                )

                next(entries)

                entry = entries.send(await controller.prompt())

    click.echo(click.style("Finishing the curation process ...", fg="yellow"))


async def curate_institutions(
    registry, Controller, Navigator, Informant, session,
):
    differences = find_institution_differences(registry, session.academine)

    provider_namespace = dict()
    institution_providers = defaultdict(set)

    for nid, namespace in registry.namespaces.items():
        for resource in namespace.resources:
            provider_namespace[resource.id] = namespace

            institution_providers[resource.institution.id].add(resource.id)

    def get_namespace_compact_identifier_link(pid):
        provider = registry.resources[pid]
        namespace = provider_namespace[pid]

        return f"[{provider.mirId if provider.providerCode == 'CURATOR_REVIEW' else provider.providerCode}/{namespace.prefix}](https://registry.identifiers.org/registry/{namespace.prefix})"

    entries = curation_entry_generator(
        differences,
        [
            partial(
                InstitutionsValidator.check_and_create,
                get_namespace_compact_identifier_link,
            )
        ],
    )

    next(entries)
    entries.send(session.position)

    click.echo(click.style("Starting the curation process ...", fg="yellow"))

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
                session.update(entry.index, entry.visited)

                for validation in entry.validations:
                    validation.format(informant)

                navigation_url = "https://registry.identifiers.org/curation"
                institution = entry.entry[1]["string"]

                await navigator.navigate(navigation_url, institution)

                await informant.output(
                    navigation_url,
                    {"type": "institution", "text": institution,},
                    "The following institutions were extracted:",
                    entry.position,
                    entry.total,
                )

                next(entries)

                entry = entries.send(await controller.prompt())

    click.echo(click.style("Finishing the curation process ...", fg="yellow"))
