from contextlib import suppress

import click
import pyppeteer

from .coordinator import PyppeteerCoordinator
from .navigator import PyppeteerNavigator


class PyppeteerInstitutionNavigator(PyppeteerNavigator):
    def __init__(self, page):
        super().__init__(page)

        self.page = page

    async def __aenter__(self):
        click.echo(
            click.style("REMEMBER:", fg="yellow")
            + " You need to be logged in as a curator on "
            + "identifiers.org to navigate to specific institutions."
        )

        return self

    async def navigate(self, url, institution_name):
        if not (
            self.page.url.startswith("https://registry.identifiers.org/curation")
            and url.startswith("https://registry.identifiers.org/curation")
        ):
            await super().navigate(url, institution_name)

        async with PyppeteerCoordinator(self.page) as coordinator:
            with suppress(
                pyppeteer.errors.ElementHandleError, pyppeteer.errors.TimeoutError
            ):
                xpath = '//input[@placeholder="Input a search query"]'
                handle = await self.page.waitForXPath(xpath, timeout=1000)
                await self.page.evaluate("handle => handle.value = ''", handle)
                await handle.type(institution_name, delay=0)

                xpath = f'//a[text()="{institution_name}"]'
                await self.page.waitForXPath(xpath, timeout=1000)

                await coordinator.evaluateScript("edit_institution.js", xpath)
