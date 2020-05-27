import asyncio
import base64
import gzip
import json
import magic
import multiprocessing as mp
import os
import random
import sys
import time
import traceback
import urllib

from async_generator import asynccontextmanager
from collections import OrderedDict
from contextlib import closing
from datetime import datetime, timezone
from os import path, listdir
from tempfile import TemporaryDirectory
from urllib.parse import urlparse, urldefrag
from xeger import Xeger

import psutil
import pyppeteer
import requests

import socket


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


import warnings

warnings.filterwarnings("ignore")


from tqdm import tqdm

from . import proxy3


def patch_pyppeteer():
    import pyppeteer.connection

    original_method = pyppeteer.connection.websockets.client.connect

    def new_method(*args, **kwargs):
        kwargs["ping_interval"] = None
        kwargs["ping_timeout"] = None
        return original_method(*args, **kwargs)

    pyppeteer.connection.websockets.client.connect = new_method

    import pyppeteer.launcher

    pyppeteer.launcher.DEFAULT_ARGS.remove("--disable-features=site-per-process")


patch_pyppeteer()


def normaliseURL(url):
    url = urldefrag(url).url

    return url[:-1] if url.endswith("/") else url


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


import re

FTP_STATUS_PATTERN = re.compile(r"([1-6][0-9][0-9])")


async def scrape_ftp_resource(url, timeout):
    request_date = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)

    request_time = time.perf_counter()

    try:
        with closing(urllib.request.urlopen(url, timeout=timeout)) as r:
            content = r.read()

            response_time = time.perf_counter() - request_time

            detected = magic.detect_from_content(content)

            redirects = [
                {
                    "url": url,
                    "ip_port": None,
                    "response_time": int(round(response_time, 3) * 1000),
                    "status": r.getcode() or 200,
                    "dns_error": False,
                    "ssl_error": False,
                    "invalid_response": False,
                }
            ]

            if detected.encoding == "binary":
                content = "data:{};base64,{}".format(
                    detected.mime_type, base64.b64encode(content).decode("utf-8")
                )
            else:
                content = content.decode(detected.encoding)

            content_type = f"{detected.mime_type}; charset={detected.encoding}"
    except Exception as err:
        match = FTP_STATUS_PATTERN.search(repr(err))

        status = None if match is None else int(match.group(1))
        status = 408 if status == 115 else status

        redirects = [
            {
                "url": url,
                "ip_port": None,
                "response_time": None,
                "status": status,
                "dns_error": status == 434,
                "ssl_error": False,
                "invalid_response": True,
            }
        ]

        content = None
        content_type = None

    return (request_date, redirects, content, content_type)


async def setup_page_monitoring(browser, page):
    await page.setUserAgent((await browser.userAgent()).replace("Headless", ""))

    responses = OrderedDict()
    redirects = set()
    finishing = set()
    failures = dict()

    prequests = dict()
    navigations = OrderedDict()

    def onRequest(request):
        prequests[request.url] = request

        finishing.add(request)

    def onResponse(response):
        url = normaliseURL(response.url)

        responses[url] = response
        responses.move_to_end(url, last=True)

        finishing.discard(response.request)

    def onRequestFinished(request):
        url = normaliseURL(request.url)

        responses[url] = request.response
        responses.move_to_end(url, last=True)

        if (300 <= request.response.status <= 399) and (len(request.redirectChain) > 0):
            redirects.add(request.redirectChain[0].url)
        elif len(request.redirectChain) > 0:
            redirects.discard(request.redirectChain[0].url)

        finishing.discard(request)

    def onRequestFailed(request):
        failures[normaliseURL(request.url)] = request.failure()

        finishing.discard(request)

    def onFrameNavigated(frame):
        if frame == page.mainFrame:
            request = prequests.get(frame.url, None)

            if request is not None:
                for r in request.redirectChain + [request]:
                    if r.url not in navigations:
                        navigations[r.url] = r.response

    page.on("request", onRequest)
    page.on("response", onResponse)
    page.on("requestfinished", onRequestFinished)
    page.on("requestfailed", onRequestFailed)
    page.on("framenavigated", onFrameNavigated)

    return (responses, redirects, finishing, failures, prequests, navigations)


async def navigate_http_resource(
    page,
    url,
    timeout,
    responses,
    redirects,
    finishing,
    failures,
    prequests,
    navigations,
):
    response = None
    content = False

    err_acc = None

    with TemporaryDirectory() as downloadPath:
        await page._client.send(
            "Page.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": downloadPath},
        )
        await page._client.send(
            "Network.enable",
            {
                "maxResourceBufferSize": 1024 * 1024 * 512,  # 512Mb
                "maxTotalBufferSize": 1024 * 1024 * 1024,  # 1GB
            },
        )

        start_time = time.time()

        request_date = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)

        try:
            response = await page.goto(
                url, timeout=(timeout * 1000), waitUntil=["domcontentloaded"]
            )

            await page.waitFor(500)

            while (len(redirects) > 0 or len(finishing) > 0) and (
                (time.time() - start_time) < timeout
            ):
                await page.waitFor(500)

            await page.waitFor(15000)

            response = True
        except pyppeteer.errors.PageError as err:
            err_acc = err

            if str(err).startswith("net::ERR_ABORTED at "):
                files = listdir(downloadPath)

                start_time = time.time()

                while len(files) != 1 and (time.time() - start_time) < 5.0:
                    await page.waitFor(500)
                    files = listdir(downloadPath)

                if len(files) == 1:
                    with open("{}/{}".format(downloadPath, files[0]), "rb") as file:
                        content = file.read()

                        detected = magic.detect_from_content(content)

                        if detected.encoding == "binary":
                            content = "data:{};base64,{}".format(
                                detected.mime_type,
                                base64.b64encode(content).decode("utf-8"),
                            )
                        else:
                            content = content.decode(detected.encoding)

                        _url, response = responses.popitem(last=True)

                        failures.pop(normaliseURL(response.url), None)
                else:
                    _url, _response = responses.popitem(last=True)

                    if (
                        _response.headers.get("x-ssl-error", False)
                        or _response.headers.get("x-invalid-response", False)
                        or _response.headers.get("x-dns-error", False)
                    ):
                        response = _response
                        content = None

                        failures.pop(normaliseURL(response.url), None)
        except Exception as err:
            err_acc = err

            response = responses.get(normaliseURL(page.url))

    if response is None:
        raise err_acc

    failure = (
        failures.get(normaliseURL(response.url))
        if not isinstance(response, bool)
        else None
    )

    if failure is not None:
        raise pyppeteer.errors.PageError(
            "{} at {}".format(failure["errorText"], response.url)
        )

    if content is False:
        content = await page.content()

    pageURL = page.url if page.url != "about:blank" else response.url

    final_request = prequests.get(pageURL, None)

    if final_request is not None:
        for r in final_request.redirectChain + [final_request]:
            if r.url not in navigations:
                navigations[r.url] = r.response

    return (request_date, navigations, content)


async def scrape_http_resource(proxy_address, timeout, url):
    while True:
        try:
            async with launch_browser(
                headless=True,
                ignoreHTTPSErrors=True,
                autoClose=False,
                args=[
                    "--no-sandbox",
                    f"--proxy-server={proxy_address}",
                    "--disable-gpu",
                ],
            ) as browser:
                async with new_page(browser) as page:
                    request_date, navigations, content = await navigate_http_resource(
                        page,
                        url,
                        timeout,
                        *(await setup_page_monitoring(browser, page)),
                    )

                break
        except (pyppeteer.errors.NetworkError, pyppeteer.errors.BrowserError):
            continue

    redirects = [
        {
            "url": k,
            "ip_port": r.headers.get("x-ip-port"),
            "response_time": int(round(float(r.headers["x-response-time"]), 3) * 1000)
            if "x-response-time" in r.headers
            else None,
            "status": r.status if r.status != requests.codes.no_content else None,
            "dns_error": bool(r.headers.get("x-dns-error", False)),
            "ssl_error": bool(r.headers.get("x-ssl-error", False)),
            "invalid_response": bool(r.headers.get("x-invalid-response", False)),
        }
        for k, r in navigations.items()
    ]

    content_type = (
        list(navigations.values())[-1].headers.get("content-type")
        if len(navigations) > 0
        else None
    )

    return (request_date, redirects, content, content_type)


from filelock import FileLock


async def fetch_resource(proxy_address, timeout, rid, lui, url):
    pings = []

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

        pings.append(
            {
                "lui": lui,
                "date": str(request_date),
                "redirects": redirects,
                "content": content,
                "content-type": content_type,
            }
        )
    except Exception:
        traceback.print_exc(file=sys.stdout)

    with FileLock("pings.lock"):
        if path.exists("dump/pings_{}.gz".format(rid)):
            with gzip.open("dump/pings_{}.gz".format(rid), "rt") as file:
                pings = json.load(file) + pings

        with gzip.open("dump/pings_{}.gz".format(rid), "wt") as file:
            json.dump(pings, file)


import logging

logging.getLogger("asyncio").setLevel(logging.CRITICAL)


def fetch_resource_sync(proxy_address, timeout, rid, lui, url):
    loop = asyncio.new_event_loop()

    try:
        coro = fetch_resource(proxy_address, timeout, rid, lui, url)

        asyncio.set_event_loop(loop)

        return loop.run_until_complete(coro)
    finally:
        loop.stop()
        loop.close()


async def scrape_resources_loop(proxy_address, jobs, timeout):
    for (rid, lui, url) in tqdm(jobs):
        await fetch_resource(proxy_address, timeout, rid, lui, url)


async def scrape_resources_pool(ctx, proxy, proxy_address, jobs, workers, timeout):
    coordinating_processes = set([proxy]) if proxy is not None else set()

    loop = asyncio.get_event_loop()

    with tqdm(total=len(jobs)) as progress:
        processes_timeout = dict()
        cleanup_timeout = dict()

        # TODO: needs to exit even if
        while len(jobs) > 0 or (
            (len(processes_timeout) > 0 or len(cleanup_timeout) > 0)
            and time.time() < final_timeout
        ):
            active_processes = set(mp.active_children()).difference(
                coordinating_processes
            )

            finished_processes = []

            with FileLock("pings.lock"):
                for process, timeout in processes_timeout.items():
                    if process not in active_processes:
                        pass
                    elif time.time() > timeout:
                        process.kill()
                    else:
                        continue

                    finished_processes.append(process)

            for _ in range(min(workers - len(active_processes), len(jobs))):
                rid, lui, url = jobs.pop()

                process = ctx.Process(
                    target=fetch_resource_sync,
                    args=(proxy_address, timeout, rid, lui, url),
                )

                processes_timeout[process] = time.time() + timeout * 3

                process.start()

                if len(jobs) == 0:
                    final_timeout = time.time() + timeout * 4

            for process in finished_processes:
                processes_timeout.pop(process)

                progress.update(1)

            child_pids = set(
                process.pid for process in psutil.Process().children(recursive=True)
            ).difference(process.pid for process in coordinating_processes)

            active_pids = set(psutil.pids())

            progress.set_postfix(
                {"child_pids": len(child_pids), "total_pids": len(active_pids)}
            )

            finished_processes = []

            with FileLock("pings.lock"):
                for pid, timeout in cleanup_timeout.items():
                    if pid not in active_pids:
                        finished_processes.append(pid)
                    elif time.time() > timeout:
                        try:
                            psutil.Process(pid=pid).kill()
                        except:
                            pass

            for process in finished_processes:
                cleanup_timeout.pop(process)

            for child in child_pids:
                if child not in cleanup_timeout:
                    cleanup_timeout[child] = time.time() + timeout * 4

            await asyncio.sleep(1)

        # Final cleanup of processes
        with FileLock("pings.lock"):
            active_processes = set(mp.active_children()).difference(
                coordinating_processes
            )

            for process, timeout in processes_timeout.items():
                if process in active_processes:
                    process.kill()

            active_pids = set(psutil.pids())

            for pid, timeout in cleanup_timeout.items():
                if pid in active_pids:
                    try:
                        psutil.Process(pid=pid).kill()
                    except:
                        pass


XEGER_LIMIT = 10


def generate_scraping_jobs(registry, num_valid, num_random, namespace_ids):
    resources = dict()

    for nid, namespace in registry.namespaces.items():
        for resource in namespace.resources:
            rid = resource.id
            url = resource.urlPattern

            resources[rid] = {
                "prefix": namespace.prefix,
                "pattern": namespace.pattern,
                "rid": rid,
                "url": url,
                "luis": set([namespace.sampleId, resource.sampleId][:num_valid]),
            }

    if num_valid > 0:
        valid_luis = 0

        for rid, resource in resources.items():
            ids = list(
                set(
                    lui
                    for lui in getattr(namespace_ids, resource["prefix"], [])
                    if lui is not None
                ).difference(resource["luis"])
            )
            random.shuffle(ids)

            resource["luis"].update(ids[: (num_valid - len(resource["luis"]))])

            valid_luis += len(resource["luis"])

        remaining_resources = list(resources.values())

        while len(remaining_resources) > 0 and valid_luis < (
            len(resources) * num_valid
        ):
            resource = remaining_resources.pop(0)

            ids = list(
                set(
                    lui
                    for lui in getattr(namespace_ids, resource["prefix"], [])
                    if lui is not None
                ).difference(resource["luis"])
            )

            if len(ids) == 0:
                continue

            random.shuffle(ids)

            num_to_add = min(
                len(ids),
                (
                    (len(resources) * num_valid)
                    - valid_luis
                    + len(remaining_resources)
                    - 1
                )
                // len(remaining_resources),
            )

            resource["luis"].update(ids[:num_to_add])

            valid_luis += num_to_add

            remaining_resources.append(resource)

    if num_random > 0:
        for rid, resource in resources.items():
            luis = resource["luis"]
            start_len = len(luis)

            pattern = resource["pattern"].replace("\\\\", "\\")

            xeg = Xeger(limit=XEGER_LIMIT)

            while len(luis) < (start_len + num_random):
                lui = xeg.xeger(pattern)

                if lui is not None:
                    luis.add(lui)

    jobs = []

    for rid, resource in resources.items():
        resource["luis"] = list(resource["luis"])

        for lui in resource["luis"]:
            jobs.append((rid, lui, resource["url"].replace("{$id}", lui)))

    random.shuffle(jobs)

    return jobs


async def scrape_resources(jobs, dump, proxy_address, workers, timeout):
    ctx = mp.get_context("spawn")

    try:
        if proxy_address is None:
            proxy_port = find_free_port()

            proxy = ctx.Process(
                target=proxy3.serve, args=(proxy_port, timeout / 3), daemon=True
            )
            proxy.start()

            proxy_address = f"localhost:{proxy_port}"
        else:
            proxy = None

        await asyncio.sleep(5)

        await scrape_resources_pool(ctx, proxy, proxy_address, jobs, workers, timeout)
    except Exception as err:
        raise err
    finally:
        if proxy is not None:
            proxy.kill()
