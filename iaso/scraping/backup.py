import asyncio
import multiprocessing as mp
import warnings

from .http.proxy_launcher import ProxyLauncher
from .pool import scrape_resources_pool


async def scrape_resources(jobs, dump, proxy_address, workers, timeout):
    ctx = mp.get_context("spawn")

    warnings.filterwarnings("ignore")

    with ProxyLauncher(ctx, timeout / 3, proxy_address) as (proxy, proxy_address):
        await asyncio.sleep(5)

        await scrape_resources_pool(ctx, proxy, proxy_address, jobs, workers, timeout)
