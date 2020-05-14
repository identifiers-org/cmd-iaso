from json import JSONEncoder

import click


def format_json(json_vals, has_next=False, indent=0, force_indent=False, nl=False):
    # Check for namedtuples and convert them into dicts
    if isinstance(json_vals, tuple) and hasattr(json_vals, "_asdict"):
        json_vals = json_vals._asdict()

    accumulator = []

    if force_indent:
        accumulator.append("  " * indent)

    if isinstance(json_vals, dict):
        accumulator.append("{\n")

        iters = json_vals.items()

        for i, (key, val) in enumerate(iters):
            accumulator.append(
                click.style(
                    "{indent}{key}: ".format(indent=("  " * (indent + 1)), key=key),
                    fg="red",
                )
            )

            accumulator.append(
                format_json(val, (i + 1) < len(iters), indent + 1, False, True)
            )

        accumulator.append("{indent}}}".format(indent=("  " * indent)))
    elif isinstance(json_vals, list):
        accumulator.append("[\n")

        for i, val in enumerate(json_vals):
            accumulator.append(
                format_json(val, (i + 1) < len(json_vals), indent + 1, True, True)
            )

        accumulator.append("{indent}]".format(indent=("  " * indent)))
    elif isinstance(json_vals, str):
        accumulator.append(
            click.style('"{value}"'.format(value=json_vals), fg="yellow")
        )
    else:
        accumulator.append(click.style("{value}".format(value=json_vals), fg="green"))

    if has_next:
        accumulator.append(",")

    if nl:
        accumulator.append("\n")

    return "".join(accumulator)
