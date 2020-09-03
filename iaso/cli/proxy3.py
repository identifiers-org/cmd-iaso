import logging

from functools import partial

import click

from ..click.docker import wrap_docker
from ..click.lazy import lazy_import

lazy_import(
    globals(),
    """
from ..scraping.http.proxy3 import serve as serve_proxy
""",
)


@click.command()
@click.pass_context
@click.option("--port", default=8080, show_envvar=True)
@click.option("--timeout", default=10, show_envvar=True)
@click.option(
    "--log",
    type=click.Choice(["null", "stderr", "proxy3.log"]),
    default="null",
    show_envvar=True,
)
@wrap_docker()
def proxy3(ctx, port, timeout, log):
    """
    Launches a new instance of the HTTPS intercepting data scraping proxy.

    --port specifies the port to run the proxy on.
    By default, port 8080 is used.

    --timeout specifies the timeout in seconds the proxy will use when
    requesting resources from the Internet.
    By default, a timeout of 10 seconds is used.

    --log specifies which logging output to use. 'null' discards all messages,
    'stderr' redirects them to stderr and 'proxy3.log' appends them to the
    proxy3.log file in the current working directory. By default, all messages
    are discarded.

    As this proxy generates a new self-signed SSL certificate to intercept
    HTTPS requests, you might get security warnings when you use this proxy.
    """
    serve_proxy(
        port,
        timeout,
        log={
            "null": logging.NullHandler,
            "stderr": logging.StreamHandler,
            "proxy3.log": partial(logging.FileHandler, "proxy3.log"),
        }[log](),
    )
