from functools import partial

from .interact import CurationController, CurationNavigator, CurationInformant
from .generator import curation_entry_generator, CurationDirection

import click


async def curate(
    registry,
    Controller,
    Navigator,
    Informant,
    tag_store,
    session,
    get_curation_data_and_validators,
    get_navigation_url_auxiliary,
    get_informant_title_description,
):
    provider_namespace = dict()

    for nid, namespace in registry.namespaces.items():
        for resource in namespace.resources:
            provider_namespace[resource.id] = namespace

    curation_data, curation_validators = get_curation_data_and_validators(
        session, registry, provider_namespace
    )

    entries = curation_entry_generator(curation_data, curation_validators)

    next(entries)
    entries.send(session.position)

    click.echo(click.style("Starting the curation process ...", fg="yellow"))

    last_direction = CurationDirection.FORWARD
    entry = entries.send(last_direction)

    last_index = None

    if entry == CurationDirection.FINISH:
        click.echo(
            click.style("There are no entries that require curation.", fg="green")
        )
    else:
        async with await CurationController.create(
            Controller
        ) as controller, await CurationNavigator.create(
            Navigator
        ) as navigator, await CurationInformant.create(
            partial(Informant, tag_store)
        ) as informant:
            while entry != CurationDirection.FINISH:
                session.update(entry.index, entry.visited)

                for validation in entry.validations:
                    validation.format(informant)

                if (
                    last_direction != CurationDirection.RELOAD
                    and not informant.check_if_non_empty_else_reset()
                ):
                    if last_index == entry.index:
                        click.echo(
                            click.style(
                                "There are no non-ignored entries that require curation.",
                                fg="yellow",
                            )
                        )

                        break

                    if last_index is None:
                        last_index = entry.index

                    next(entries)

                    entry = entries.send(last_direction)

                    continue

                last_index = None

                navigation_url, navigation_auxiliary = get_navigation_url_auxiliary(
                    entry, registry, provider_namespace
                )
                await navigator.navigate(navigation_url, navigation_auxiliary)

                (
                    informant_title,
                    informant_description,
                ) = get_informant_title_description(entry, registry, provider_namespace)
                await informant.output(
                    navigation_url,
                    informant_title,
                    informant_description,
                    entry.position,
                    entry.total,
                )

                next(entries)

                last_direction = await controller.prompt()
                entry = entries.send(last_direction)

    click.echo(click.style("Finishing the curation process ...", fg="yellow"))
