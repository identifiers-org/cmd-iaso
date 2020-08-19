import asyncio
import gzip
import json
import logging
import os
import pickle
import signal
import sys
import traceback
import warnings

from urllib.parse import urlparse

from filelock import FileLock

from .ftp import scrape_ftp_resource
from .http import scrape_http_resource


def fetch_resource_worker(
    dump,
    proxy_address,
    chrome,
    timeout,
    tempdir,
    scraping_pings_lock,
    log,
    rid,
    lui,
    random,
    url,
):
    try:
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        loop = asyncio.new_event_loop()

        coro = fetch_resource(
            dump,
            proxy_address,
            chrome,
            timeout,
            tempdir,
            scraping_pings_lock,
            rid,
            lui,
            random,
            url,
        )

        asyncio.set_event_loop(loop)

        logging.getLogger("asyncio").setLevel(logging.CRITICAL + 1)
        warnings.filterwarnings("ignore")

        return loop.run_until_complete(coro)
    except:
        if log != "null":
            if os.path.exists(scraping_pings_lock):
                with FileLock(scraping_pings_lock):
                    try:
                        if log == "stderr":
                            logf = sys.stderr
                        else:
                            logf = open("scrape.log", "a")

                        logf.write(
                            f"Error at rid={rid} lui={lui} url={url} random={random}:\n"
                        )

                        traceback.print_exc(file=logf)
                    finally:
                        if log == "scrape.log":
                            logf.close()


async def fetch_resource(
    dump,
    proxy_address,
    chrome,
    timeout,
    tempdir,
    scraping_pings_lock,
    rid,
    lui,
    random,
    url,
):
    try:
        parsed = urlparse(url)

        if parsed.scheme == "http" or parsed.scheme == "https":
            request_date, redirects, content, content_type = await asyncio.wait_for(
                scrape_http_resource(tempdir, proxy_address, chrome, timeout, url),
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

        if os.path.exists(scraping_pings_lock):
            with FileLock(scraping_pings_lock):
                with gzip.open(dump / f"pings_{rid}.gz", "ab") as file:
                    pickle.dump(ping, file)

                with open(dump / "PROGRESS", "a") as file:
                    json.dump((rid, lui, random, url), file)

    except asyncio.TimeoutError:
        pass
