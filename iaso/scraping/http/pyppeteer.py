import pyppeteer

from async_generator import asynccontextmanager

from . import patch_pyppeteer

patch_pyppeteer.patch_pyppeteer()


def patch_pyppeteer():
    original_connect = pyppeteer.connection.websockets.client.connect

    def new_connect(*args, **kwargs):
        kwargs["ping_interval"] = None
        kwargs["ping_timeout"] = None

        return original_connect(*args, **kwargs)

    pyppeteer.connection.websockets.client.connect = new_connect

    if "--disable-features=site-per-process" in pyppeteer.launcher.DEFAULT_ARGS:
        pyppeteer.launcher.DEFAULT_ARGS.remove("--disable-features=site-per-process")


patch_pyppeteer()


@asynccontextmanager
async def launch_browser(options=None, **kwargs):
    try:
        browser = await pyppeteer.launch(options, **kwargs)

        yield browser
    finally:
        try:
            await browser.close()
        except:
            pass


@asynccontextmanager
async def new_page(browser):
    try:
        context = await browser.createIncognitoBrowserContext()
        page = await context.newPage()

        yield page
    finally:
        try:
            await context.close()
        except:
            pass
