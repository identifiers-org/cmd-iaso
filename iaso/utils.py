from json import JSONEncoder

import click


def echo_json(json_vals, has_next=False, indent=0, force_indent=False):
    # Check for namedtuples and convert them into dicts
    if isinstance(json_vals, tuple) and hasattr(json_vals, "_asdict"):
        json_vals = json_vals._asdict()

    if force_indent:
        click.echo("  " * indent, nl=False)

    if isinstance(json_vals, dict):
        click.echo("{")

        iters = json_vals.items()

        for i, (key, val) in enumerate(iters):
            click.echo(
                click.style(
                    "{indent}{key}: ".format(indent=("  " * (indent + 1)), key=key),
                    fg="red",
                ),
                nl=False,
            )

            echo_json(val, (i + 1) < len(iters), indent + 1, False)

        click.echo("{indent}}}".format(indent=("  " * indent)), nl=False)
    elif isinstance(json_vals, list):
        click.echo("[")

        for i, val in enumerate(json_vals):
            echo_json(val, (i + 1) < len(json_vals), indent + 1, True)

        click.echo("{indent}]".format(indent=("  " * indent)), nl=False)
    elif isinstance(json_vals, str):
        click.echo(
            click.style('"{value}"'.format(value=json_vals), fg="yellow"), nl=False
        )
    else:
        click.echo(click.style("{value}".format(value=json_vals), fg="green"), nl=False)

    click.echo("," if has_next else "")
