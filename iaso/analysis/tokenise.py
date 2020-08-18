from functools import partial
from multiprocessing.pool import ThreadPool

from athena import tokenise_and_join_with_spaces


def tokenise_pings(inner_progress, pings):
    inner_progress.set_description("Tokensising scraped responses")
    inner_progress.reset(total=len(pings))

    luis = []
    contents = []
    https = []

    for ping in pings:
        luis.append(ping["lui"])
        contents.append(ping["content"] if ping["content"] is not None else None)
        https.append(
            ping["redirects"][-1]["status"] if len(ping["redirects"]) > 0 else None
        )

    lowered_luis = set(luis)
    lowered_luis.update(lui.lower() for lui in luis)

    extended_luis = set()

    for lui in lowered_luis:
        extended_luis.add(lui)

        if "#" in lui:
            extended_luis.add(lui[: lui.find("#")])

            for to in range(lui.find("#") + 1):
                if not lui[to].isalnum():
                    break

            extended_luis.add(lui[:to])

    exclusions = list(extended_luis)

    tokens = [None for _ in range(len(contents))]

    def callback(index, combined_tokens):
        tokens[index] = combined_tokens
        inner_progress.update()

    def error(err):
        raise err

    with ThreadPool() as pool:
        for index, content in enumerate(contents):
            if content is None:
                continue

            pool.apply_async(
                tokenise_and_join_with_spaces,
                (content, exclusions),
                {},
                partial(callback, index),
                error,
            )

        pool.close()
        pool.join()

    return luis, tokens, https
