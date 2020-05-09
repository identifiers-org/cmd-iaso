import asyncio
import click
import sys

import pyppeteer

from contextlib import suppress

from ..interact import CurationNavigator


class PyppeteerNavigator(CurationNavigator):
    def __init__(self, page):
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

        try:
            if sys.version_info >= (3, 7):
                loop = asyncio.get_running_loop()
            else:
                loop = asyncio.get_event_loop()
        except RuntimeError:  # There is no current event loop
            loop = None

        if loop and loop.is_running():
            loop.create_task(self.hackRedirectConnection(callFrameId))
        else:
            asyncio.run(self.hackRedirectConnection(callFrameId))

    async def navigate(self, url):
        if self.page.url.startswith(
            "https://registry.identifiers.org"
        ) and url.startswith("https://registry.identifiers.org"):
            # Attempt to hijack SPA redirects for smoother redirection
            self.redirectPath = url[32:].replace("registry", "registri")

            with suppress(pyppeteer.errors.NetworkError):
                await self.page.click("[href='/registry']")

            self.redirectPath = url[32:]

            with suppress(pyppeteer.errors.NetworkError):
                await self.page.click("[href='/registry']")

            with suppress(pyppeteer.errors.NetworkError):
                await self.page.mouse.move(0, 0)

            return

        await self.page.goto(url)
