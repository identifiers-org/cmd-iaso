import asyncio
import logging
import os
import shutil
import tempfile

from datetime import datetime, timezone

os.environ["PYPPETEER_CHROMIUM_REVISION"] = "782078"

from pyppeteer import errors as pyppeteer_errors
from requests import codes as status_code_values

from .navigate import navigate_http_resource
from .pyppeteer import launch_browser, new_page
from .request_monitor import setup_page_monitoring


async def scrape_http_resource(tempdir, proxy_address, chrome, timeout, url):
    logging.getLogger("pyppeteer").setLevel(logging.CRITICAL + 1)

    while True:
        try:
            options = {}

            if chrome is not None:
                options["executablePath"] = chrome

            try:
                userDataDir = tempfile.mkdtemp(dir=tempdir)

                async with launch_browser(
                    headless=True,
                    ignoreHTTPSErrors=True,
                    userDataDir=userDataDir,
                    autoClose=True,
                    handleSIGINT=False,
                    handleSIGTERM=False,
                    handleSIGHUP=False,
                    args=[
                        "--no-sandbox",
                        f"--proxy-server={proxy_address}",
                        "--disable-gpu",
                    ],
                    **options,
                ) as browser:
                    async with new_page(browser) as page:
                        (
                            request_date,
                            navigations,
                            content,
                            content_type,
                        ) = await navigate_http_resource(
                            tempdir,
                            page,
                            url,
                            timeout,
                            *(await setup_page_monitoring(browser, page)),
                        )

                    break
            finally:
                for retry in range(100):
                    if os.path.exists(userDataDir):
                        shutil.rmtree(userDataDir, ignore_errors=True)

                        if os.path.exists(userDataDir):
                            await asyncio.sleep(0.01)
                    else:
                        break
        except pyppeteer_errors.TimeoutError:
            return (
                datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None),
                [
                    {
                        "url": url,
                        "ip_port": None,
                        "response_time": int(round(float(timeout), 3) * 1000),
                        "status": status_code_values.timeout,
                        "dns_error": False,
                        "ssl_error": False,
                        "invalid_response": False,
                    }
                ],
                None,
                None,
            )
        except (
            pyppeteer_errors.BrowserError,
            pyppeteer_errors.NetworkError,
            pyppeteer_errors.PageError,
        ):
            continue

    redirects = [
        {
            "url": k,
            "ip_port": r.headers.get("x-ip-port"),
            "response_time": int(round(float(r.headers["x-response-time"]), 3) * 1000)
            if "x-response-time" in r.headers
            else None,
            "status": r.status
            if r.status != status_code_values.no_content
            else status_code_values.request_timeout
            if bool(r.headers.get("x-request-timeout", False))
            else None,
            "dns_error": bool(r.headers.get("x-dns-error", False)),
            "ssl_error": bool(r.headers.get("x-ssl-error", False)),
            "invalid_response": bool(r.headers.get("x-invalid-response", False)),
        }
        for k, r in navigations.items()
    ]

    return (request_date, redirects, content, content_type)
