from collections import OrderedDict

from requests import codes as status_code_values

from .url import normaliseURL


async def setup_page_monitoring(browser, page):
    await page.setUserAgent((await browser.userAgent()).replace("Headless", ""))

    responses = OrderedDict()  # Request responses ordered by their arrival
    redirects = set()  # Set of running redirection requests
    finishing = set()  # Set of running requests
    failures = dict()  # Failed requests

    prequests = dict()  # All requests made
    navigations = OrderedDict()  # Redirection chain

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

        if (
            status_code_values.multiple_choices
            <= request.response.status
            < status_code_values.bad_request
        ) and (len(request.redirectChain) > 0):
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
