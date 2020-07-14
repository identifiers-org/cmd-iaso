import re

from json import JSONEncoder

import click

LINK_PATTERN = re.compile(r"<(.+?)>")
NAMED_LINK_PATTERN = re.compile(r"\[(.+?)\]\((.+?)\)")


def format_json(json_vals, has_next=False, indent=0, force_indent=False, nl=False):
    # Check for namedtuples and convert them into dicts
    if isinstance(json_vals, tuple) and hasattr(json_vals, "_asdict"):
        json_vals = json_vals._asdict()

    accumulator = []

    if force_indent:
        accumulator.append("  " * indent)

    if isinstance(json_vals, dict):
        if json_vals.get("__rich__", False) is True:
            accumulator.append(
                click.style(
                    json_vals["text"],
                    **{
                        k: v
                        for k, v in json_vals.items()
                        if k not in ["__rich__", "text"]
                    }
                )
            )
        else:
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
    elif isinstance(json_vals, list) or isinstance(json_vals, tuple):
        accumulator.append("[\n")

        for i, val in enumerate(json_vals):
            accumulator.append(
                format_json(val, (i + 1) < len(json_vals), indent + 1, True, True)
            )

        accumulator.append("{indent}]".format(indent=("  " * indent)))
    elif isinstance(json_vals, str):
        for i, text in enumerate(LINK_PATTERN.split(json_vals)):
            if i % 2 == 0:
                for i, text in enumerate(NAMED_LINK_PATTERN.split(text)):
                    if i % 3 == 0:
                        accumulator.append(click.style(text, fg="yellow"))
                    elif i % 3 == 1:
                        # Named links cannot be copy-pasted, so they are formatted as normal text
                        accumulator.append(click.style(text, fg="yellow"))
            else:
                accumulator.append(click.style(text, fg="bright_blue", underline=True))
    else:
        accumulator.append(click.style("{value}".format(value=json_vals), fg="green"))

    if has_next:
        accumulator.append(",")

    if nl:
        accumulator.append("\n")

    return "".join(accumulator)
