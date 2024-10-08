import asyncio

from functools import update_wrapper

import click


def coroutine(f):
    # f = asyncio.run(f)

    def wrapper(*args, **kwargs):
        ctx = click.get_current_context()
        ctx.obj["loop"] = asyncio.get_event_loop()
        return ctx.obj["loop"].run_until_complete(f(*args, **kwargs))

    return update_wrapper(wrapper, f)
