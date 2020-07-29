import asyncio

from importlib.resources import read_text


def read_package_data_file(path):
    return read_text("iaso.curation.pyppeteer", path)


class PyppeteerCoordinator:
    lock = asyncio.Lock()

    addStyleTagWithIdHelper = read_package_data_file("style.js")
    addScriptTagWithIdHelper = read_package_data_file("script.js")

    def __init__(self, page):
        self.page = page

    async def __aenter__(self):
        await PyppeteerCoordinator.lock.__aenter__()

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await PyppeteerCoordinator.lock.__aexit__(exc_type, exc_value, traceback)

    async def addStyleTagWithId(self, path, sid):
        await self.page.evaluate(
            PyppeteerCoordinator.addStyleTagWithIdHelper,
            read_package_data_file(path),
            sid,
        )

    async def addScriptTagWithId(self, path, sid):
        await self.page.evaluate(
            PyppeteerCoordinator.addScriptTagWithIdHelper,
            read_package_data_file(path),
            sid,
        )

    async def evaluate(self, path, *args):
        await self.page.evaluate(read_package_data_file(path), *args)
