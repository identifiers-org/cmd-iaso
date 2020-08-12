import asyncio
import gzip
import logging
import pickle
import sys
import traceback
import warnings

from urllib.parse import urlparse

from filelock import FileLock

from .ftp import scrape_ftp_resource
from .http import scrape_http_resource


def fetch_resource_worker(
    dump, proxy_address, chrome, timeout, tempdir, rid, lui, random, url
):
    loop = asyncio.new_event_loop()

    try:
        coro = fetch_resource(
            dump, proxy_address, chrome, timeout, tempdir, rid, lui, random, url
        )

        asyncio.set_event_loop(loop)

        logging.getLogger("asyncio").setLevel(logging.CRITICAL + 1)
        warnings.filterwarnings("ignore")

        return loop.run_until_complete(coro)
    finally:
        loop.stop()
        loop.close()


async def fetch_resource(
    dump, proxy_address, chrome, timeout, tempdir, rid, lui, random, url
):
    try:
        parsed = urlparse(url)

        if parsed.scheme == "http" or parsed.scheme == "https":
            request_date, redirects, content, content_type = await asyncio.wait_for(
                scrape_http_resource(proxy_address, chrome, timeout, url),
                timeout=(timeout * 2),
            )
        elif parsed.scheme == "ftp":
            request_date, redirects, content, content_type = await asyncio.wait_for(
                scrape_ftp_resource(url, timeout), timeout=(timeout * 2)
            )
        else:
            raise Exception(f"Unknown resource scheme {parsed.scheme}")

        ping = {
            "lui": lui,
            "random": random,
            "date": str(request_date),
            "redirects": redirects,
            "content": content,
            "content-type": content_type,
        }

        with FileLock(tempdir / "pings.lock"):
            with gzip.open(dump / f"pings_{rid}.gz", "ab") as file:
                pickle.dump(ping, file)
    except asyncio.TimeoutError:
        pass
    except Exception:
        with FileLock(tempdir / "pings.lock"):
            log.write(f"Error at rid={rid} lui={lui} url={url} random={random}")

            with open("scraper.log", "a") as log:
                traceback.print_exc(file=log)
