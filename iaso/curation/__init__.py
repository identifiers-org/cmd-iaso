import click

from ..utils import format_json
from .validators.http_status_error import HTTPStatusError
from .interact import CurationController, CurationNavigator, CurationFormatter
from .generator import curation_entry_generator, CurationDirection


async def curate(registry, datamine, Controller, Navigator, Informant):
    click.echo("The data loaded was collected in the following environment:")
    click.echo(format_json(datamine.environment))

    provider_namespace = dict()

    for nid, namespace in registry.namespaces.items():
        for resource in namespace.resources:
            provider_namespace[resource.id] = namespace

    entries = curation_entry_generator(
        datamine.providers,
        [lambda p: p.id in registry.resources, HTTPStatusError.check_and_create],
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

                await navigator.navigate(navigation_url)

                await informant.output(
                    navigation_url, provider, namespace, entry.position, entry.total
                )

                next(entries)

                entry = entries.send(await controller.prompt())

    click.echo(click.style("Finishing the curation process ...", fg="yellow"))
