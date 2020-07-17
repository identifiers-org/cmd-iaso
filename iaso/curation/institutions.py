from functools import partial

from ..institutions.differences import find_institution_differences
from ..institutions.validator import InstitutionsValidator

from . import curate


def get_curation_data_and_validators_institutions(
    session, registry, provider_namespace
):
    differences = find_institution_differences(registry, session.academine)

    def get_namespace_compact_identifier_link(pid):
        provider = registry.resources[pid]
        namespace = provider_namespace[pid]

        return f"[{provider.mirId if provider.providerCode == 'CURATOR_REVIEW' else provider.providerCode}/{namespace.prefix}](https://registry.identifiers.org/registry/{namespace.prefix})"

    return (
        differences,
        [
            partial(
                InstitutionsValidator.check_and_create,
                get_namespace_compact_identifier_link,
            )
        ],
    )


def get_navigation_url_auxiliary_institutions(entry, registry, provider_namespace):
    return ("https://registry.identifiers.org/curation", entry.entry[1]["string"])


def get_informant_title_description_institutions(entry, registry, provider_namespace):
    institution = entry.entry[1]["string"]

    return (
        {"type": "institution", "text": institution},
        "The following institutions were extracted:",
    )


async def curate_institutions(
    registry, Controller, Navigator, Informant, tag_store, session,
):
    await curate(
        registry,
        Controller,
        Navigator,
        Informant,
        tag_store,
        session,
        get_curation_data_and_validators_institutions,
        get_navigation_url_auxiliary_institutions,
        get_informant_title_description_institutions,
    )
