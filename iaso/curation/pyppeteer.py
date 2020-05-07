import pyppeteer
import requests

import asyncio
import click

from .interact import CurationController, CurationNavigator, CurationFormatter


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

        try:
            await self.page.close()
        except:
            pass

        if self.address == "launch":
            try:
                await self.page.browser.close()
            except:
                pass
        else:
            try:
                await self.page.browser.disconnect()
            except:
                pass

    async def connect(self):
        if self.page is not None:
            return

        if self.address == "launch":
            click.echo(click.style("Launching the Chrome browser ...", fg="yellow"))

            browser = await pyppeteer.launch()

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

        self.page = await browser.newPage()

    def warp(self, Creator):
        async def create(*args, **kwargs):
            await self.connect()

            return Creator(self.page, *args, **kwargs)

        return create


class PyppeteerController(CurationController):
    def __init__(self, page):
        self.page = page
        self.prompt_future = None
        self.redirectPath = None

    async def connect(self):
        async def onclose():
            if self.prompt_future is not None:
                self.prompt_future.set_result(None)

        async def onnavigate(frame):
            try:
                header_inserted = (
                    not self.page.url.startswith("https://registry.identifiers.org")
                ) or (
                    await self.page.evaluate(
                        "document.body.firstElementChild.id === 'iaso-header'"
                    )
                )
            except:
                header_inserted = True

            if not header_inserted:
                try:
                    await self.page.addStyleTag(
                        content="""
                        html::-webkit-scrollbar {
                            display: none;
                        }
                        
                        #iaso-header {
                            display: block;
                            height: 264px;
                            width: 125px;
                            position: fixed;
                            z-index: 9;
                            top: calc(50% - 120px);
                            bottom: calc(50% - 120px);
                            left: 20px;
                            overflow-x: hidden;
                            pointer-events: none;

                        }

                        .iaso-button {
                            border-radius: 4px;
                            background-color: white;
                            border: 2px solid #4CAF50;
                            color: black;
                            padding: 10px 0px;
                            text-align: center;
                            display: inline-block;
                            font-size: 18px;
                            transition-duration: 0.4s;
                            width: 125px;
                            pointer-events: auto;
                        }

                        .iaso-button + .iaso-button {
                            margin-top: 20px;
                        }

                        .iaso-button:hover {
                            background-color: #4CAF50;
                            color: white;
                        }

                        #iaso-overlay {
                            position: fixed;
                            display: none;
                            overflow-y: scroll;
                            width: 100%;
                            height: 100%;
                            top: 0;
                            left: 0;
                            right: 0;
                            bottom: 0;
                            background-color: rgba(0, 0, 0, 0.75);
                            z-index: 10;
                        }
                        
                        #iaso-overlay::-webkit-scrollbar {
                            display: none;
                        }

                        #iaso-overlay-content {
                            cursor: default;
                            margin: 10px;
                        }

                        #iaso-overlay-issues {
                            list-style-type: none;
                            pointer-events: none;
                        }

                        #iaso-overlay-issues > li {
                            color: white;
                            #pointer-events: none;
                        }

                        #iaso-overlay-issues > li:before {
                            content: "-";
                            margin-left: -1ch;
                            margin-right: 1ch;
                        }

                        .disclosure, .syntax, .string, .number, .boolean, .key, .keyword, .object.syntax, .array.syntax, .object.syntax + a, .array.syntax + a {
                            background-color: white;
                            pointer-events: auto;
                        }

                        .disclosure, .object.syntax + a, .array.syntax + a {
                            #pointer-events: auto;
                        }

                        .string {
                            color: purple;
                        }

                        .number, .boolean, .keyword {
                            color: darkgreen;
                        }

                        .key {
                            color: red;
                        }
                    """
                    )

                    with open(
                        "{path}/../deps/renderjson/renderjson.js".format(
                            path=pathlib.Path(__file__).parent
                        ),
                        "r",
                    ) as file:
                        await self.page.addScriptTag(content=file.read())

                    await self.page.evaluate(
                        """{
                        if (document.getElementById("iaso-overlay") === null) {
                            const overlay = document.createElement('div');
                            overlay.id = "iaso-overlay";

                            overlay.innerHTML = `
                                <div id="iaso-overlay-content">
                                    <h3 style="color: orange">Curation required for resource provider <span id="iaso-overlay-provider" style="font-weight: bold">[NOT A PROVIDER]</span> <span id="iaso-overlay-index" style="color: white"></span>:</h3>
                                    <h4 style="color: white">The following issues were observed:</h4>
                                    <ul id="iaso-overlay-issues">
                                        <li>The curation browser has not yet been navigated to a problematic resource provider.</li>
                                        <li>Please exit the information overlay and navigate to the next or previous problematic provider.</li>
                                    </ul>
                                </div>
                            `;

                            overlay.onclick = function () {
                                document.getElementById("iaso-overlay").style.display = 'none';
                                document.getElementById('iaso-header').style.display = 'block';
                                const scrollY = document.body.scrollTop;
                                document.body.style.overflow = 'initial';
                                document.body.style.height = 'auto';
                                document.scrollingElement.scrollTop = scrollY;
                            };

                            document.body.insertBefore(overlay, document.body.firstElementChild);
                        }

                        if (document.getElementById("iaso-header") === null) {
                            const header = document.createElement('div');
                            header.id = "iaso-header";

                            header.innerHTML = `
                                <button class="iaso-button" onclick="{ document.getElementById('iaso-overlay').style.display = 'block'; document.getElementById('iaso-header').style.display = 'none'; const scrollY = document.scrollingElement.scrollTop; document.body.style.overflow = 'hidden'; document.body.style.height = '100vh'; document.body.scrollTop = scrollY; }">Information</button>
                                <button class="iaso-button" onclick="console.info('iaso-fw')">Forward</button>
                                <button class="iaso-button" onclick="console.info('iaso-bw')">Backward</button>
                                <button class="iaso-button" onclick="console.info('iaso-end')">End Session</button>
                            `;

                            document.body.insertBefore(header, document.body.firstElementChild);
                        }
                    }"""
                    )
                except:  # Exception as err:
                    pass
                    # print("PyppeteerController.onnavigate Error:", err)

        def onconsole(console):
            if (
                console.type == "info"
                and console.text.startswith("iaso-")
                and console.text[5:] in TerminalController.CHOICES
            ):
                if self.prompt_future is not None:
                    self.prompt_future.set_result(
                        TerminalController.CHOICES[console.text[5:]]
                    )

        self.browser = await pyppeteer.connect(
            browserWSEndpoint=(await self.initiator()),
            defaultViewport={"width": 0, "height": 0},
        )
        self.page = await self.browser.newPage()

        self.page.on("framenavigated", onnavigate)
        self.page.on("close", onclose)
        self.page.on("console", onconsole)

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

        async def hackRedirectConnection(callFrameId):
            if self.redirectPath is not None:
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

        def handleBreakpoint(context):
            callFrameId = context["callFrames"][0]["callFrameId"]

            try:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:  # RuntimeError: There is no current event loop..
                    loop = None

                if loop and loop.is_running():
                    loop.create_task(hackRedirectConnection(callFrameId))
                else:
                    asyncio.run(hackRedirectConnection(callFrameId))
            except:  # Exception as err:
                pass
                # print("PyppeteerController.handleBreakpoint Error:", err)

        self.page._client.on("Debugger.paused", handleBreakpoint)

    async def navigate(self, url):
        if self.page.url.startswith(
            "https://registry.identifiers.org"
        ) and url.startswith("https://registry.identifiers.org"):
            self.redirectPath = url[32:].replace("registry", "registri")

            await self.page.click("[href='/registry']")

            self.redirectPath = url[32:]

            await self.page.click("[href='/registry']")

            await self.page.mouse.move(0, 0)
        else:
            await self.page.goto(url)

    async def prompt(self):
        self.prompt_future = Future()

        prompt = await self.prompt_future

        self.prompt_future = None

        return prompt

    async def disconnect(self):
        try:
            await self.page.close()
        except:
            pass

        if self.closeondisconnect:
            try:
                await self.browser.close()
            except:
                pass


class PyppeteerNavigator(CurationNavigator):
    def __init__(self, page):
        self.page = page

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

        self.page._client.on("Debugger.paused", self.handleBreakpoint)

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

    def handleBreakpoint(self, context):
        callFrameId = context["callFrames"][0]["callFrameId"]

        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:  # There is no current event loop
                loop = None

            if loop and loop.is_running():
                loop.create_task(self.hackRedirectConnection(callFrameId))
            else:
                asyncio.run(self.hackRedirectConnection(callFrameId))
        except:
            pass

    async def navigate(self, url):
        if self.page.url.startswith(
            "https://registry.identifiers.org"
        ) and url.startswith("https://registry.identifiers.org"):
            # Attempt to hijack SPA redirects for smoother redirection
            try:
                self.redirectPath = url[32:].replace("registry", "registri")

                await self.page.click("[href='/registry']")

                self.redirectPath = url[32:]

                await self.page.click("[href='/registry']")

                await self.page.mouse.move(0, 0)

                return
            except:
                pass

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
            try:
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
            except:  # Exception as err:
                pass
                # print("PyppeteerFormatter.refresh Error:", err)
