import os

from .pyppeteer import launch_browser, new_page
from .navigate import navigate_http_resource
from .request_monitor import setup_page_monitoring

from pyppeteer import errors as pyppeteer_errors
from requests import codes as status_code_values


async def scrape_http_resource(proxy_address, chrome, timeout, url):
    while True:
        try:
            options = {}

            if chrome is not None:
                options["executablePath"] = chrome

            async with launch_browser(
                headless=True,
                ignoreHTTPSErrors=True,
                acceptInsecureCerts=True,
                autoClose=False,
                args=[
                    "--no-sandbox",
                    f"--proxy-server={proxy_address}",
                    "--disable-gpu",
                    "--ignore-certificate-errors",
                    "--ignore-certificate-errors-spki-list",
                    "--enable-features=NetworkService",
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
                        page,
                        url,
                        timeout,
                        *(await setup_page_monitoring(browser, page)),
                    )

                break
        except (pyppeteer_errors.NetworkError, pyppeteer_errors.BrowserError):
            continue

    redirects = [
        {
            "url": k,
            "ip_port": r.headers.get("x-ip-port"),
            "response_time": int(round(float(r.headers["x-response-time"]), 3) * 1000)
            if "x-response-time" in r.headers
            else None,
            "status": r.status if r.status != status_code_values.no_content else None,
            "dns_error": bool(r.headers.get("x-dns-error", False)),
            "ssl_error": bool(r.headers.get("x-ssl-error", False)),
            "invalid_response": bool(r.headers.get("x-invalid-response", False)),
        }
        for k, r in navigations.items()
    ]

    return (request_date, redirects, content, content_type)
