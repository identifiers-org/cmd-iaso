from textwrap import fill as wrap

import click


def report_statistics(ok_entries, ig_entries, ok_issues, ig_issues):
    ctx = click.get_current_context()

    width = 80 if ctx.max_content_width is None else ctx.max_content_width

    title = "Curation Statistics"
    center_str = "_" * len(title)

    click.echo(
        " {} ".format(center_str)
        .center(width, "=")
        .replace(center_str, click.style(title, fg="green"))
    )

    click.echo()

    entries_str = (
        f"{ok_entries + ig_entries} "
        + f"entr{'y' if (ok_entries + ig_entries) == 1 else 'ies'}"
    )
    ignored_str = (
        "none" if ig_entries == 0 else "one" if ig_entries == 1 else ig_entries
    )

    click.echo(
        wrap(
            (
                "In response to the current settings, {entries} {entries_were} "
                + "identified for curation, {ignored} of which {ignored_were} ignored because "
                + "of their issues' tags."
            ).format(
                entries=entries_str,
                entries_were=("was" if (ok_entries + ig_entries) == 1 else "were"),
                ignored=ignored_str,
                ignored_were=("was" if ig_entries == 1 else "were"),
            ),
            width=width,
        )
        .replace(entries_str, click.style(entries_str, fg="yellow"))
        .replace("curation", click.style("curation", fg="yellow"))
        .replace(ignored_str, click.style(ignored_str, fg="green"))
        .replace("ignored", click.style("ignored", fg="green"))
    )
    click.echo()

    click.echo(
        wrap("The following issue types were identified for curation:", width=width)
    )

    for issue_type, count in (ok_issues + ig_issues).most_common():
        ignored_str = f"{ig_issues[issue_type]} ignored"

        click.echo(
            wrap(
                f"- {issue_type}: {count} ({ignored_str})",
                width=width,
                subsequent_indent="    ",
            )
            .replace(issue_type, click.style(issue_type, underline=True))
            .replace(str(count), click.style(str(count), fg="yellow"))
            .replace(ignored_str, click.style(ignored_str, fg="green"))
        )

    click.echo()

    click.echo("=" * (80 if ctx.max_content_width is None else ctx.max_content_width))
