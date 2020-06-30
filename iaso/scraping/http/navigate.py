import os
import time

from datetime import datetime, timezone
from tempfile import TemporaryDirectory

import pyppeteer

from .url import normaliseURL
from ..content_type import get_mime_type, get_encoding, get_content_type, decode_content


def build_html_from_dom(ele):
    content = [ele["nodeValue"]]

    if "children" in ele:
        content.extend(build_html_from_dom(child) for child in ele["children"])

    if "shadowRoots" in ele:
        content.extend(build_html_from_dom(root) for root in ele["shadowRoots"])

    # if 'pseudoElements' in ele:
    #    content.extend(build_html_from_dom(pseudo) for pseudo in ele['pseudoElements'])

    content = " ".join(content)

    if ele["localName"] == "":
        return content
    else:
        return f'<{ele["localName"]}>{content}</{ele["localName"]}>'


async def navigate_http_resource(
    page,
    url,
    timeout,
    responses,
    redirects,
    finishing,
    failures,
    requests,
    navigations,
):
    response = None

    content = False
    content_type = None

    err_acc = None

    with TemporaryDirectory() as downloadPath:
        # Enable downloading to a temporary downloadPath
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
            # Wait until the landing HTTP page has been loaded
            response = await page.goto(
                url, timeout=(timeout * 1000), waitUntil=["domcontentloaded"]
            )

            await page.waitFor(500)

            # Wait for additional HTTP requests to finish, but at most for timeout
            while (len(redirects) > 0 or len(finishing) > 0) and (
                (time.time() - start_time) < timeout
            ):
                await page.waitFor(500)

            # Give dynamic webpages time to load their content
            await page.waitFor(timeout / 2)

            response = True
        except pyppeteer.errors.PageError as err:
            err_acc = err

            if str(err).startswith("net::ERR_ABORTED at "):
                files = os.listdir(downloadPath)

                start_time = time.time()

                while len(files) != 1 and (time.time() - start_time) < (timeout / 6):
                    await page.waitFor(500)
                    files = os.listdir(downloadPath)

                if len(files) == 1:
                    # The browser has downloaded a file
                    with open("{}/{}".format(downloadPath, files[0]), "rb") as file:
                        content = file.read()

                        _url, response = responses.popitem(last=True)

                        mime_type = get_mime_type(content, response.url)
                        encoding = get_encoding(content)

                        content_type = get_content_type(mime_type, encoding)
                        content = decode_content(content, mime_type, encoding)

                        failures.pop(normaliseURL(response.url), None)
                else:
                    _url, _response = responses.popitem(last=True)

                    if (
                        _response.headers.get("x-ssl-error", False)
                        or _response.headers.get("x-invalid-response", False)
                        or _response.headers.get("x-dns-error", False)
                        or _response.headers.get("x-request-timeout", False)
                    ):
                        # The scraping proxy has responded with a destructive error message
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
        # Raise uncaught Chrome browser failures (could be added as special cases)
        raise pyppeteer.errors.PageError(
            "{} at {}".format(failure["errorText"], response.url)
        )

    if content is False:
        # Fetch the entire DOM of the loaded page, including the shadow DOMs
        dom = (
            await page._client.send("DOM.getDocument", {"pierce": True, "depth": -1})
        )["root"]

        content = build_html_from_dom(dom)

    pageURL = page.url if page.url != "about:blank" else response.url

    final_request = requests.get(pageURL, None)

    # Finalise the main redirection chain
    if final_request is not None:
        for r in final_request.redirectChain + [final_request]:
            if r.url not in navigations:
                navigations[r.url] = r.response

    if content is not None:
        # Extract the content-type if the content exists
        header_content_type = (
            list(navigations.values())[-1].headers.get("content-type")
            if len(navigations) > 0
            else None
        )

        if header_content_type is not None:
            content_type = header_content_type

        if content_type is None:
            mime_type = get_mime_type(content.encode("utf-8"), pageURL)
            encoding = "utf-8"

            content_type = get_content_type(mime_type, encoding)

    return (request_date, navigations, content, content_type)
