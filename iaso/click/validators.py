import pkg_resources

import click

from ..curation.validator import CurationValidator


def load_registered_validators(ctx):
    ctx.obj["validators"] = {
        entry_point.name: entry_point
        for entry_point in pkg_resources.iter_entry_points("iaso.plugins")
    }


def validate_validators(ctx, param, value):
    validators = dict()

    for validator_name in set(value):
        Validator = ctx.obj["validators"].get(validator_name, None)

        if Validator is None:
            raise click.BadParameter(
                f"{validator_name} is not a registered validator plugin in 'iaso.plugins'."
            )

        if isinstance(Validator, pkg_resources.EntryPoint):
            Validator = Validator.load()

            if not issubclass(Validator, CurationValidator):
                raise click.BadParameter(
                    f"{validator_name} does not export a subclass of 'iaso.curation.validator.CurationValidator'."
                )

            if len(Validator.__abstractmethods__) > 0:
                raise click.BadParameter(
                    f"{validator_name} does not export a non-abstract subclass of 'iaso.curation.validator.CurationValidator'."
                )

            ctx.obj["validators"][validator_name] = Validator

        validators[validator_name] = Validator

    return validators


def list_validators(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    if len(ctx.obj["validators"]) == 0:
        click.echo(
            "No validator modules have been registered under 'iaso.plugins' yet."
        )
    else:
        click.echo(
            "The following validator modules have been registered under 'iaso.plugins':"
        )

    for validator in ctx.obj["validators"]:
        click.echo(f"- {validator}")

    ctx.exit()
