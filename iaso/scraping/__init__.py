import asyncio
import logging
import multiprocessing as mp
import signal
import warnings

from pyppeteer.chromium_downloader import check_chromium, download_chromium

from .http.patch_pyppeteer import patch_pyppeteer
from .http.proxy_launcher import ProxyLauncher
from .pool import scrape_resources_pool


async def scrape_resources(jobs, dump, proxy_address, chrome, workers, timeout):
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    if chrome is None:
        if not check_chromium():
            patch_pyppeteer()
            download_chromium()

    ctx = mp.get_context("spawn")

    logging.getLogger("asyncio").setLevel(logging.CRITICAL + 1)
    warnings.filterwarnings("ignore")

    with ProxyLauncher(ctx, timeout / 3, proxy_address) as (proxy, proxy_address):
        await asyncio.sleep(5)

        await scrape_resources_pool(
            ctx, dump, proxy, proxy_address, chrome, jobs, workers, timeout
        )
