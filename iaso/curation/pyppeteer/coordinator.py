import asyncio
import pathlib

from importlib.resources import read_text


class PyppeteerCoordinator:
    lock = asyncio.Lock()

    def __read_file(path):
        return read_text("iaso.curation.pyppeteer", path)

    addStyleTagWithIdHelper = __read_file("style.js")
    addScriptTagWithIdHelper = __read_file("script.js")

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
            PyppeteerCoordinator.__read_file(path),
            sid,
        )

    async def addScriptTagWithId(self, path, sid):
        await self.page.evaluate(
            PyppeteerCoordinator.addScriptTagWithIdHelper,
            PyppeteerCoordinator.__read_file(path),
            sid,
        )

    async def evaluate(self, path, *args):
        await self.page.evaluate(PyppeteerCoordinator.__read_file(path), *args)
