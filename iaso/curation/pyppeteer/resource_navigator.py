from contextlib import suppress

import click
import pyppeteer

from .coordinator import PyppeteerCoordinator
from .navigator import PyppeteerNavigator


class PyppeteerResourceNavigator(PyppeteerNavigator):
    def __init__(self, page):
        super().__init__(page)

        self.page = page
        self.redirectPath = None

    async def __aenter__(self):
        # Inject a breakpoint right before the React Router redirects

        # Use the Chrome Developer Tools Sources tab to find the location
        # - Go to the https://registry.identifiers.org/ subdomain
        # - Set a breakpoint at /node_modules/react-router-dom/es/Link.js line 52
        # - Click on either the 'Registry' or 'Browse the registry' button
        # - Find the location at the top of the callstack in the local scope
        #   in the handleBreakpoint context
        await self.page._client.send(
            "Debugger.setBreakpointByUrl",
            {
                "lineNumber": 194,
                "url": "https://registry.identifiers.org/src.9524714e.js",
                "columnNumber": 1543,
            },
        )
        await self.page._client.send("Debugger.enable", {})
        await self.page._client.send("Debugger.setBreakpointsActive", {"active": True})

        self.page._client.on("Debugger.paused", self.onBreakpoint)

        return self

    async def hackRedirectConnection(self, callFrameId):
        if self.redirectPath is not None:
            # Use the Chrome Developer Tools Sources tab to find the variable name
            # - Go to the https://registry.identifiers.org/ subdomain
            # - Set a breakpoint at /node_modules/react-router-dom/es/Link.js line 52
            # - Click on either the 'Registry' or 'Browse the registry' button
            # - Click on the link at the bottom right (source mapped from LINK)
            # - Pretty print the file (bottom left curly brackets)
            # - Extract the name of the parameter to replace(p) and push(p)
            await self.page._client.send(
                "Debugger.setVariableValue",
                {
                    "scopeNumber": 0,
                    "variableName": "a",
                    "newValue": {"value": self.redirectPath},
                    "callFrameId": callFrameId,
                },
            )

            self.redirectPath = None

        await self.page._client.send("Debugger.resume", {})

    def onBreakpoint(self, context):
        callFrameId = context["callFrames"][0]["callFrameId"]

        click.get_current_context().obj["loop"].create_task(
            self.hackRedirectConnection(callFrameId)
        )

    async def navigate(self, url, provider_id):
        if self.page.url.startswith(
            "https://registry.identifiers.org"
        ) and url.startswith("https://registry.identifiers.org"):
            with suppress(pyppeteer.errors.NetworkError):
                await self.page.click("[href='/registry']")

            self.redirectPath = url[32:].replace("registry", "registri")

            with suppress(pyppeteer.errors.NetworkError):
                await self.page.click("[href='/registry']")

            self.redirectPath = url[32:]

            with suppress(pyppeteer.errors.NetworkError):
                await self.page.click("[href='/registry']")

            with suppress(pyppeteer.errors.NetworkError):
                await self.page.mouse.move(0, 0)
        else:
            await super().navigate(url, provider_id)

        # Enter edit mode for the current provider information
        async with PyppeteerCoordinator(self.page) as coordinator:
            with suppress(
                pyppeteer.errors.ElementHandleError, pyppeteer.errors.TimeoutError
            ):
                xpath = f'//td[text()="{provider_id}"]'

                await self.page.waitForXPath(xpath, timeout=1000)

                await coordinator.evaluateScript("edit_resource.js", xpath)
