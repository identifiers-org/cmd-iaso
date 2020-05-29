import asyncio
import gzip
import pickle
import sys
import traceback

from urllib.parse import urlparse

from filelock import FileLock

from .http import scrape_http_resource
from .ftp import scrape_http_resource


def fetch_resource_worker(proxy_address, timeout, tempdir, rid, lui, url):
    loop = asyncio.new_event_loop()

    try:
        coro = fetch_resource(proxy_address, timeout, tempdir, rid, lui, url)

        asyncio.set_event_loop(loop)

        return loop.run_until_complete(coro)
    finally:
        loop.stop()
        loop.close()


async def fetch_resource(proxy_address, timeout, tempdir, rid, lui, url):
    try:
        parsed = urlparse(url)

        if parsed.scheme == "http" or parsed.scheme == "https":
            request_date, redirects, content, content_type = await asyncio.wait_for(
                scrape_http_resource(proxy_address, timeout, url), timeout=(timeout * 2)
            )
        elif parsed.scheme == "ftp":
            request_date, redirects, content, content_type = await asyncio.wait_for(
                scrape_ftp_resource(url, timeout), timeout=(timeout * 2)
            )
        else:
            raise Exception(f"Unknown resource scheme {parsed.scheme}")

        ping = {
            "lui": lui,
            "date": str(request_date),
            "redirects": redirects,
            "content": content,
            "content-type": content_type,
        }

        with FileLock(tempdir / "pings.lock"):
            with gzip.open("dump/pings_{}.gz".format(rid), "ab") as file:
                pickle.dump(ping, file)

    except Exception:
        traceback.print_exc(file=sys.stdout)
