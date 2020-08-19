import asyncio
import logging
import multiprocessing as mp
import os
import warnings

from pathlib import Path
from tempfile import TemporaryDirectory

os.environ["PYPPETEER_CHROMIUM_REVISION"] = "782078"

from .http.proxy_launcher import ProxyLauncher
from .pool import scrape_resources_pool


async def scrape_resources(
    jobs, total_jobs, dump, proxy_address, chrome, workers, timeout, log
):
    if chrome is None:
        from pyppeteer.chromium_downloader import check_chromium, download_chromium

        from .http.patch_pyppeteer import patch_pyppeteer

        if not check_chromium():
            patch_pyppeteer()
            download_chromium()

    ctx = mp.get_context("spawn")

    logging.getLogger("asyncio").setLevel(logging.CRITICAL + 1)
    warnings.filterwarnings("ignore")

    # Open encompassing temporary directory for scraping
    with TemporaryDirectory() as tempdir:
        dump = Path(dump)
        tempdir = Path(tempdir)

        with ProxyLauncher(ctx, timeout / 3, proxy_address, tempdir) as (
            proxy,
            proxy_address,
        ):
            await asyncio.sleep(5)

            await scrape_resources_pool(
                ctx,
                dump,
                tempdir,
                proxy,
                proxy_address,
                chrome,
                jobs,
                total_jobs,
                workers,
                timeout,
                log,
            )
