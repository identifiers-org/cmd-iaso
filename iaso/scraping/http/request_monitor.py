from collections import OrderedDict

from requests import codes as status_code_values

from .url import normaliseURL


async def setup_page_monitoring(browser, page):
    await page.setUserAgent((await browser.userAgent()).replace("Headless", ""))

    prequests = dict()  # All requests made
    responses = OrderedDict()  # Request responses ordered by their arrival
    failures = dict()  # Failed requests
    navigations = OrderedDict()  # Redirection chain

    def onRequest(request):
        prequests[request.url] = request

    def onResponse(response):
        url = normaliseURL(response.url)

        responses[url] = response
        responses.move_to_end(url, last=True)

    def onRequestFinished(request):
        url = normaliseURL(request.url)

        responses[url] = request.response
        responses.move_to_end(url, last=True)

    def onRequestFailed(request):
        failures[normaliseURL(request.url)] = request.failure()

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

    return (prequests, responses, failures, navigations)
