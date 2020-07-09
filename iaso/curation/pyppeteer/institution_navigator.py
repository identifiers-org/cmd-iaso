# import click

# import pyppeteer

# from contextlib import suppress

from .navigator import PyppeteerNavigator

# from .coordinator import PyppeteerCoordinator


class PyppeteerResourceNavigator(PyppeteerNavigator):
    def __init__(self, page):
        super().__init__(page)

    async def navigate(self, url, institution_name):
        if not (
            page.url.startswith("https://registry.identifiers.org/curation")
            and url.startswith("https://registry.identifiers.org/curation")
        ):
            await super().navigate(url, institution_name)

        async with PyppeteerCoordinator(page) as coordinator:
            with suppress(
                pyppeteer.errors.ElementHandleError, pyppeteer.errors.TimeoutError
            ):
                xpath = '//input[@placeholder="Input a search query"]'
                handle = await page.waitForXPath(xpath, timeout=1000)
                await handle.type(institution_name)

                xpath = '//span[text()="1 to 1 of 1"]'
                await page.waitForXPath(xpath, timeout=1000)

                xpath = f'//a[text()="{institution_name}"]'
                await page.waitForXPath(xpath, timeout=1000)

                await coordinator.evaluate("edit_institution.js", xpath)
