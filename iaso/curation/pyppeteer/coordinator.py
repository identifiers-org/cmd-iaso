import asyncio
import pathlib


class PyppeteerCoordinator:
    lock = asyncio.Lock()

    with open(f"{pathlib.Path(__file__).parent}/style.js", "r") as file:
        addStyleTagWithIdHelper = file.read()

    with open(f"{pathlib.Path(__file__).parent}/script.js", "r") as file:
        addScriptTagWithIdHelper = file.read()

    def __init__(self, page):
        self.page = page

    async def __aenter__(self):
        await PyppeteerCoordinator.lock.__aenter__()

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await PyppeteerCoordinator.lock.__aexit__(exc_type, exc_value, traceback)

    async def addStyleTagWithId(self, path, sid):
        with open(f"{pathlib.Path(__file__).parent}/{path}", "r") as file:
            await self.page.evaluate(
                PyppeteerCoordinator.addStyleTagWithIdHelper, file.read(), sid
            )

    async def addScriptTagWithId(self, path, sid):
        with open(f"{pathlib.Path(__file__).parent}/{path}", "r") as file:
            await self.page.evaluate(
                PyppeteerCoordinator.addScriptTagWithIdHelper, file.read(), sid
            )

    async def evaluate(self, path, *args):
        with open(f"{pathlib.Path(__file__).parent}/{path}", "r") as file:
            await self.page.evaluate(file.read(), *args)
