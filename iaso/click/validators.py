import click

try:
    from importlib.metadata import entry_points, EntryPoint

    def iter_entry_points(path):
        return entry_points().get(path, [])


except ImportError:
    # Running on pre-3.8 Python
    from pkg_resources import iter_entry_points, EntryPoint

from ..curation.validator import CurationValidator


def ensure_registered_validators(ctx):
    registered_validators = ctx.obj.get("validators")

    if registered_validators is None:
        registered_validators = ctx.obj["validators"] = {
            entry_point.name: entry_point
            for entry_point in iter_entry_points("iaso.plugins")
        }

    return registered_validators


def validate_validators(ctx, param, value):
    registered_validators = ensure_registered_validators(ctx)

    validators = dict()

    for validator_string in set(value):
        [validator_name, *validator_params] = validator_string.split(":", 1)

        Validator = registered_validators.get(validator_name, None)

        if Validator is None:
            raise click.BadParameter(
                f"{validator_name} is not a registered validator plugin in 'iaso.plugins'."
            )

        if isinstance(Validator, EntryPoint):
            Validator = Validator.load()

            if len(validator_params) > 0:
                validator_params = {
                    param.split("=", 1)[0].strip(): (
                        param.split("=", 1)[1:] or (True,)
                    )[0]
                    for param in validator_params[0].split(",")
                    if len(param.split("=", 1)[0].strip()) > 0
                }
            else:
                validator_params = dict()

            if not issubclass(Validator, CurationValidator):
                raise click.BadParameter(
                    f"{validator_name} does not export a subclass of 'iaso.curation.validator.CurationValidator'."
                )

            if len(Validator.__abstractmethods__) > 0:
                raise click.BadParameter(
                    f"{validator_name} does not export a non-abstract subclass of 'iaso.curation.validator.CurationValidator'."
                )

            registered_validators[validator_name] = Validator

            validators[validator_string] = Validator.validate_params(
                validator_name, **validator_params
            )

    return validators


def list_validators(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    registered_validators = ensure_registered_validators(ctx)

    if len(registered_validators) == 0:
        click.echo(
            "No validator modules have been registered under 'iaso.plugins' yet."
        )
    else:
        click.echo(
            "The following validator modules have been registered under 'iaso.plugins':"
        )

    for validator in registered_validators:
        click.echo(f"- {validator}")

    ctx.exit()
