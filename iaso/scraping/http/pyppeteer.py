import pyppeteer

from async_generator import asynccontextmanager

from . import patch_pyppeteer

patch_pyppeteer.patch_pyppeteer()


@asynccontextmanager
async def launch_browser(options=None, **kwargs):
    try:
        browser = await pyppeteer.launch(options, **kwargs)

        yield browser
    except Exception as err:
        raise pyppeteer.errors.BrowserError(err)
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
