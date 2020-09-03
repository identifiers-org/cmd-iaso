import json

from collections import Counter

import click


def filter_completed_jobs(jobs, progress_path):
    click.echo("Checking for already completed jobs ...")

    with open(progress_path, "r") as file:
        progress = file.read()

    json_decoder = json.JSONDecoder()
    json_parse_pos = 0

    completed_jobs = Counter()

    try:
        while json_parse_pos < len(progress):
            parsed, json_len = json_decoder.raw_decode(progress[json_parse_pos:])

            completed_jobs.update((tuple(parsed),))

            json_parse_pos += json_len
    except Exception as err:
        raise click.UsageError(
            click.style(f"{progress_path} has been corrupted.", fg="red")
        )

    filtered_jobs = []

    for job in jobs:
        job = tuple(job)

        if completed_jobs[job] > 0:
            completed_jobs[job] -= 1
        else:
            filtered_jobs.append(job)

    return filtered_jobs
