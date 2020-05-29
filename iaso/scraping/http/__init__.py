import pyppeteer

from .pyppeteer import launch_browser, new_page


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

    return (request_date, redirects, content, content_type)
