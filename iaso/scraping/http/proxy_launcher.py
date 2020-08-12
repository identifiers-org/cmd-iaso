import socket

from contextlib import closing

from . import proxy3


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


class ProxyLauncher:
    def __init__(self, ctx, timeout, proxy_address):
        self.ctx = ctx
        self.timeout = timeout

        self.proxy_address = proxy_address
        self.proxy = None

    def __enter__(self):
        if self.proxy_address is None:
            proxy_port = find_free_port()

            self.proxy = self.ctx.Process(
                target=proxy3.serve,
                args=(proxy_port, self.timeout),
                kwargs={"ignore_sigint": True},
                daemon=True,
            )
            self.proxy.start()

            self.proxy_address = f"localhost:{proxy_port}"

        return (self.proxy, self.proxy_address)

    def __exit__(self, type, value, traceback):
        if self.proxy is not None:
            self.proxy.kill()

            self.proxy = None
