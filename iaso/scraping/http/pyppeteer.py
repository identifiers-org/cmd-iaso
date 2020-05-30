import pyppeteer

from async_generator import asynccontextmanager


def patch_pyppeteer():
    original_method = pyppeteer.connection.websockets.client.connect

    def new_method(*args, **kwargs):
        kwargs["ping_interval"] = None
        kwargs["ping_timeout"] = None
        return original_method(*args, **kwargs)

    pyppeteer.connection.websockets.client.connect = new_method

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
