import click

import pyppeteer

from contextlib import suppress

from .navigator import PyppeteerNavigator
from .coordinator import PyppeteerCoordinator


class PyppeteerResourceNavigator(PyppeteerNavigator):
    def __init__(self, page):
        super().__init__(page)

        self.redirectPath = None

    async def __aenter__(self):
        # Inject a breakpoint right before the React Router redirects

        page = super().page

        # Use the Chrome Developer Tools Sources tab to find the location
        # - Go to the https://registry.identifiers.org/ subdomain
        # - Set a breakpoint at /node_modules/react-router-dom/es/Link.js line 52
        # - Click on either the 'Registry' or 'Browse the registry' button
        # - Find the location at the top of the callstack in the local scope
        #   in the handleBreakpoint context
        await page._client.send(
            "Debugger.setBreakpointByUrl",
            {
                "lineNumber": 194,
                "url": "https://registry.identifiers.org/src.9524714e.js",
                "columnNumber": 1543,
            },
        )
        await page._client.send("Debugger.enable", {})
        await page._client.send("Debugger.setBreakpointsActive", {"active": True})

        page._client.on("Debugger.paused", self.onBreakpoint)

        return self

    async def hackRedirectConnection(self, callFrameId):
        page = super().page

        if self.redirectPath is not None:
            # Use the Chrome Developer Tools Sources tab to find the variable name
            # - Go to the https://registry.identifiers.org/ subdomain
            # - Set a breakpoint at /node_modules/react-router-dom/es/Link.js line 52
            # - Click on either the 'Registry' or 'Browse the registry' button
            # - Click on the link at the bottom right (source mapped from LINK)
            # - Pretty print the file (bottom left curly brackets)
            # - Extract the name of the parameter to replace(p) and push(p)
            await page._client.send(
                "Debugger.setVariableValue",
                {
                    "scopeNumber": 0,
                    "variableName": "a",
                    "newValue": {"value": self.redirectPath},
                    "callFrameId": callFrameId,
                },
            )

            self.redirectPath = None

        await page._client.send("Debugger.resume", {})

    def onBreakpoint(self, context):
        callFrameId = context["callFrames"][0]["callFrameId"]

        click.get_current_context().obj["loop"].create_task(
            self.hackRedirectConnection(callFrameId)
        )

    async def navigate(self, url, provider_id):
        page = super().page

        if page.url.startswith("https://registry.identifiers.org") and url.startswith(
            "https://registry.identifiers.org"
        ):
            with suppress(pyppeteer.errors.NetworkError):
                await page.click("[href='/registry']")

            self.redirectPath = url[32:].replace("registry", "registri")

            with suppress(pyppeteer.errors.NetworkError):
                await page.click("[href='/registry']")

            self.redirectPath = url[32:]

            with suppress(pyppeteer.errors.NetworkError):
                await page.click("[href='/registry']")

            with suppress(pyppeteer.errors.NetworkError):
                await page.mouse.move(0, 0)
        else:
            await super().navigate(url, provider_id)

        # Enter edit mode for the current provider information
        async with PyppeteerCoordinator(page) as coordinator:
            with suppress(
                pyppeteer.errors.ElementHandleError, pyppeteer.errors.TimeoutError
            ):
                xpath = f'//td[text()="{provider_id}"]'

                await page.waitForXPath(xpath, timeout=1000)

                await coordinator.evaluate("edit_resource.js", xpath)
