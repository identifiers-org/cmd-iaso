import click

from ..click.lazy import lazy_import
from ..click.docker import wrap_docker

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
@wrap_docker()
def proxy3(ctx, port, timeout):
    """
    Launches a new instance of the HTTPS intercepting data scraping proxy.
    
    --port specifies the port to run the proxy on.
    By default, port 8080 is used.
    
    --timeout specifies the timeout in seconds the proxy will use when
    requesting resources from the Internet.
    By default, a timeout of 10 seconds is used.
    
    As this proxy generates a new self-signed SSL certificate to intercept
    HTTPS requests, you might get security warnings when you use this proxy.
    """
    serve_proxy(port, timeout)
