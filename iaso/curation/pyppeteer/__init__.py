import pyppeteer
import requests

import click

from contextlib import suppress


def patch_pyppeteer():
    import pyppeteer.connection

    original_connect = pyppeteer.connection.websockets.client.connect

    def new_connect(*args, **kwargs):
        kwargs["ping_interval"] = None
        kwargs["ping_timeout"] = None

        return original_connect(*args, **kwargs)

    pyppeteer.connection.websockets.client.connect = new_connect

    import pyppeteer.browser

    original_create = pyppeteer.browser.Browser.create

    def new_create(*args, **kwargs):
        if "appMode" in kwargs:
            kwargs["appMode"] = False
        else:
            args_list = list(args)
            args_list[3] = False
            args = tuple(args_list)

        return original_create(*args, **kwargs)

    pyppeteer.browser.Browser.create = new_create


patch_pyppeteer()


class PyppeteerLauncher:
    def __init__(self, address):
        self.address = address
        self.page = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.page is None:
            return

        click.echo(
            click.style("Disconnecting from the Chrome browser ...", fg="yellow")
        )

        with suppress(pyppeteer.errors.PageError):
            await self.page.close()

        if self.address == "launch":
            with suppress(pyppeteer.errors.BrowserError):
                await self.page.browser.close()
        else:
            with suppress(pyppeteer.errors.BrowserError):
                await self.page.browser.disconnect()

    async def connect(self):
        if self.page is not None:
            return

        if self.address == "launch":
            click.echo(click.style("Launching the Chrome browser ...", fg="yellow"))

            browser = await pyppeteer.launch(headless=False)

            wsEndpoint = browser.wsEndpoint
        else:
            click.echo(click.style("Contacting the Chrome browser ...", fg="yellow"))

            with requests.get(f"http://{self.address}/json/version") as r:
                token = r.json()["webSocketDebuggerUrl"].split("/")[-1]

            wsEndpoint = f"ws://{self.address}/devtools/browser/{token}"

        click.echo(click.style("Connecting to the Chrome browser ...", fg="yellow"))

        browser = await pyppeteer.connect(
            browserWSEndpoint=wsEndpoint,
            # defaultViewport=None,
        )

        if self.address == "launch":
            pages = await browser.pages()

            if len(pages) > 0:
                self.page = pages[-1]

        if self.page is None:
            self.page = await browser.newPage()

    def warp(self, Creator):
        async def create(*args, **kwargs):
            await self.connect()

            return Creator(self.page, *args, **kwargs)

        return create
