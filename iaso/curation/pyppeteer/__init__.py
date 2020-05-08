import pyppeteer
import requests

import asyncio
import click
import sys
import pathlib
import re

from asyncio import Future
from contextlib import suppress

from ..interact import CurationController, CurationNavigator, CurationFormatter
from ..generator import CurationDirection


def patch_pyppeteer():
    import pyppeteer.connection

    original_connect = pyppeteer.connection.websockets.client.connect

    def new_connect(*args, **kwargs):
        kwargs["ping_interval"] = None
        kwargs["ping_timeout"] = None

        return original_connect(*args, **kwargs)

    pyppeteer.connection.websockets.client.connect = new_connect

    import pyppeteer.browser

    original_create = pyppeteer.browser.Browser.create

    def new_create(*args, **kwargs):
        if "appMode" in kwargs:
            kwargs["appMode"] = False
        else:
            args_list = list(args)
            args_list[3] = False
            args = tuple(args_list)

        return original_create(*args, **kwargs)

    pyppeteer.browser.Browser.create = new_create


patch_pyppeteer()


class PyppeteerLauncher:
    def __init__(self, address):
        self.address = address
        self.page = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.page is None:
            return

        click.echo(
            click.style("Disconnecting from the Chrome browser ...", fg="yellow")
        )

        with suppress(pyppeteer.errors.PageError):
            await self.page.close()

        if self.address == "launch":
            with suppress(pyppeteer.errors.BrowserError):
                await self.page.browser.close()
        else:
            with suppress(pyppeteer.errors.BrowserError):
                await self.page.browser.disconnect()

    async def connect(self):
        if self.page is not None:
            return

        if self.address == "launch":
            click.echo(click.style("Launching the Chrome browser ...", fg="yellow"))

            browser = await pyppeteer.launch(headless=False)

            wsEndpoint = browser.wsEndpoint
        else:
            click.echo(click.style("Contacting the Chrome browser ...", fg="yellow"))

            with requests.get(f"http://{self.address}/json/version") as r:
                token = r.json()["webSocketDebuggerUrl"].split("/")[-1]

            wsEndpoint = f"ws://{self.address}/devtools/browser/{token}"

        click.echo(click.style("Connecting to the Chrome browser ...", fg="yellow"))

        browser = await pyppeteer.connect(
            browserWSEndpoint=wsEndpoint,
            # defaultViewport=None,
        )

        if self.address == "launch":
            pages = await browser.pages()

            if len(pages) > 0:
                self.page = pages[-1]

        if self.page is None:
            self.page = await browser.newPage()

    def warp(self, Creator):
        async def create(*args, **kwargs):
            await self.connect()

            return Creator(self.page, *args, **kwargs)

        return create


class PyppeteerController(CurationController):
    def __init__(self, page, url_regex=None):
        self.page = page
        self.url_regex = re.compile(
            url_regex
            if url_regex is not None
            else r"^https:\/\/registry\.identifiers\.org.*$"
        )

        self.lock = asyncio.Lock()

        self.prompt_future = None

    async def __aenter__(self):
        self.page.on("framenavigated", self.onnavigate)
        self.page.on("close", self.onclose)
        self.page.on("console", self.onconsole)

        await self.onnavigate(None)

        return self

    def onclose(self):
        if self.prompt_future is not None:
            self.prompt_future.set_result(CurationDirection.FINISH)

    async def onnavigate(self, frame):
        async with self.lock:
            with suppress(pyppeteer.errors.NetworkError):
                display_controller = self.url_regex.match(self.page.url) is not None

                if display_controller:
                    with open(f"{pathlib.Path(__file__).parent}/style.js", "r") as file:
                        addStyleTagWithId = file.read()

                    with open(f"{pathlib.Path(__file__).parent}/iaso.css", "r") as file:
                        await self.page.evaluate(
                            addStyleTagWithId, file.read(), "iaso-style"
                        )

                    with open(
                        f"{pathlib.Path(__file__).parent}/controller.css", "r"
                    ) as file:
                        await self.page.evaluate(
                            addStyleTagWithId, file.read(), "iaso-controller-style"
                        )

                with open(
                    f"{pathlib.Path(__file__).parent}/controller.js", "r"
                ) as file:
                    await self.page.evaluate(
                        file.read(),
                        display_controller,
                        *CurationController.CHOICES.keys(),
                    )

    def onconsole(self, console):
        if (
            console.type == "info"
            and console.text.startswith("iaso-")
            and console.text[5:] in CurationController.CHOICES
        ):
            if self.prompt_future is not None:
                self.prompt_future.set_result(
                    CurationController.CHOICES[console.text[5:]]
                )

    async def prompt(self):
        self.prompt_future = Future()

        prompt = await self.prompt_future

        self.prompt_future = None

        return prompt


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

            await self.page.click("[href='/registry']")

            self.redirectPath = url[32:]

            await self.page.click("[href='/registry']")

            await self.page.mouse.move(0, 0)

            return

        await self.page.goto(url)


class PyppeteerFormatter(CurationFormatter):
    def __init__(self, page):
        self.page = page
        self.buffer = []
        self.url = ""
        self.cache = ""

        async def onnavigate(frame):
            await self.refresh()

        self.page.on("framenavigated", onnavigate)

    def format_json(self, title, content):
        self.buffer.append((title, content))

    async def output(self, url, resource, namespace, position, total):
        self.url = url

        self.cache = (
            """{
            const overlay_provider = document.getElementById("iaso-overlay-provider");
            overlay_provider.innerHTML = '"""
            + resource.name
            + """';

            const overlay_index = document.getElementById("iaso-overlay-index");
            overlay_index.innerHTML = '"""
            + "({} / {})".format(position + 1, total)
            + """';

            const noclick = function(element) {
                if (element.onclick === null) {
                    element.onclick = (element.classList.length > 0) ? function(e) {
                        e.stopPropagation();
                    } : function() {
                        document.getElementById('iaso-overlay').click();
                    };
                }

                if (element.classList.length == 0) {
                    element.style.cursor = "default";
                    element.style.pointerEvents = "auto";
                }

                for (const child of element.children) {
                    noclick(child);
                }
            };

            renderjson.set_show_to_level("all");

            const overlay_issues = document.getElementById("iaso-overlay-issues");
            overlay_issues.innerHTML = "";

            for (const [key, value] of ["""
            + ", ".join(
                "['{}', '{}']".format(key, json.dumps(value))
                for key, value in self.buffer
            )
            + """]) {
                const list = document.createElement('li');
                list.innerHTML = `<span style="text-decoration: underline">${key}: </span>`;
                const rendered_json = renderjson(JSON.parse(value));
                noclick(rendered_json);
                list.appendChild(rendered_json);
                overlay_issues.appendChild(list);
            }
        }"""
        )

        self.buffer.clear()

        await self.refresh()

    async def refresh(self):
        if self.page.url == self.url:
            await self.page.waitForSelector("#iaso-overlay")

            await self.page.evaluate(self.cache)

            await self.page.evaluate(
                """{
                document.getElementById('iaso-overlay').style.display = 'block';
                document.getElementById('iaso-header').style.display = 'none';
                const scrollY = document.scrollingElement.scrollTop;
                document.body.style.overflow = 'hidden';
                document.body.style.height = '100vh';
                document.body.scrollTop = scrollY;
            }"""
            )
