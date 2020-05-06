import asyncio
import bisect
import json
import pathlib

from abc import ABC, abstractmethod
from asyncio import Future
from collections import namedtuple, Counter

import click
import pyppeteer

from requests.status_codes import _codes as status_codes

from .utils import echo_json


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


class CurationController(ABC):
    @staticmethod
    def create(Controller, *args, **kwargs):
        ctrl = Controller(*args, **kwargs)

        super(type(ctrl), ctrl).__init__()

        return ctrl

    def __init__(self):
        pass

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def navigate(self, url):
        pass

    @abstractmethod
    async def prompt(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    def create_formatter(self, Formatter, *args, **kwargs):
        return CurationFormatter.create(Formatter, *args, **kwargs)


class TerminalController(CurationController):
    CHOICES = {"fw": +1, "bw": -1, "end": None}

    async def connect(self):
        pass

    async def navigate(self, url):
        pass

    async def prompt(self):
        direction = click.prompt(
            "Continue curation", type=click.Choice(TerminalController.CHOICES.keys())
        )

        return TerminalController.CHOICES[direction]

    async def disconnect(self):
        pass


import requests


class PyppeteerController(CurationController):
    def Launch(*args, **kwargs):
        async def launcher():
            browser = await pyppeteer.launch()

            return browser.wsEndpoint

        return PyppeteerController(launcher, True, *args, **kwargs)

    def Connect(address):
        async def connecter():
            with requests.get(f"http://{address}/json/version") as r:
                token = r.json()["webSocketDebuggerUrl"].split("/")[-1]

                return f"ws://{address}/devtools/browser/{token}"

        def launch(*args, **kwargs):
            return PyppeteerController(connecter, False, *args, **kwargs)

        return launch

    def __init__(self, initiator, closeondisconnect):
        self.initiator = initiator
        self.prompt_future = None
        self.closeondisconnect = closeondisconnect
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

    def create_formatter(self, Formatter, *args, **kwargs):
        if Formatter == PyppeteerFormatter:
            kwargs["page"] = self.page

        return super().create_formatter(Formatter, *args, **kwargs)


class CurationFormatter(ABC):
    @staticmethod
    def create(Formatter, *args, **kwargs):
        fmt = Formatter(*args, **kwargs)

        super(type(fmt), fmt).__init__()

        return fmt

    def __init__(self):
        pass

    @abstractmethod
    def format_json(self, title, content):
        pass

    @abstractmethod
    async def output(self, url, resource, namespace, position, total):
        pass


class TerminalFormatter(CurationFormatter):
    def __init__(self):
        self.buffer = []

    def format_json(self, title, content):
        self.buffer.append((title, content))

    async def output(self, url, resource, namespace, position, total):
        ctx = click.get_current_context()

        click.echo(
            " {} / {} ".format(position + 1, total).center(
                80 if ctx.max_content_width is None else ctx.max_content_width, "="
            )
        )

        click.echo(
            "{}{}{}".format(
                click.style("Curation required for resource provider ", fg="yellow"),
                click.style(resource.name, fg="yellow", bold=True),
                click.style(":", fg="yellow"),
            )
        )
        click.echo("  {}".format(click.style(url, fg="bright_blue", underline=True,)))

        click.echo("The following issues were observed:")

        for title, content in self.buffer:
            click.echo("- {}: ".format(click.style(title, underline=True)), nl=False)

            echo_json(content, indent=1)

        click.echo(
            " {} / {} ".format(position + 1, total).center(
                80 if ctx.max_content_width is None else ctx.max_content_width, "="
            )
        )

        self.buffer.clear()


class PyppeteerFormatter(CurationFormatter):
    def __init__(self, page=None):
        self.page = page
        self.buffer = []
        self.url = ""
        self.cache = ""

        # TODO: Rewrite so that page can never be None
        if self.page is not None:

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
        if self.page is not None and self.page.url == self.url:
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


class CurationError(ABC):
    @staticmethod
    @abstractmethod
    def check_and_create(provider):
        pass

    @abstractmethod
    def format(self, formatter):
        pass


class HTTPStatusError(CurationError):
    @staticmethod
    def check_and_create(provider):
        status_codes = Counter(
            [
                ping.redirects[-1].status
                for ping in provider.pings
                if len(ping.redirects) > 0
            ]
        )

        if len(status_codes) == 0:
            return True

        status_code, frequency = status_codes.most_common(1)[0]

        # TODO: redirects should also not be allowed here
        if status_code < 400:
            return True

        return HTTPStatusError(status_code)

    def __init__(self, status_code):
        self.status_code = status_code

    def format(self, formatter):
        formatter.format_json(
            "Status code",
            "{} ({})".format(
                self.status_code,
                ", ".join(
                    code.replace("_", " ")
                    for code in status_codes[self.status_code]
                    if "\\" not in code
                ),
            ),
        )
        formatter.format_json(
            "Test JSON Data",
            {
                "hello": [1, 2, 3, 4],
                "bye": [4, 3, 2, 1],
                "there": {
                    "a": 1,
                    "b": 2,
                    "c": ["hello", None],
                    "there": {"a": 1, "b": 2, "c": ["hello", None]},
                },
            },
        )


CurationEntry = namedtuple(
    "CurationEntry", ("entry", "validations", "position", "total")
)


def curation_entries(entries, validators):
    wrap = len(entries)
    index = 0

    indices = []
    non_indices = set()

    while True:
        direction = yield

        if direction != +1 and direction != -1:
            yield None

            continue

        start_index = index

        if len(indices) > 0:
            index = (index + direction) % wrap

        while True:
            validations = []

            for validator in validators:
                validation = validator(entries[index])

                if validation == False:
                    validations.clear()

                    break

                if validation == True:
                    continue

                if isinstance(validation, list):
                    validations.extend(validation)
                else:
                    validations.append(validation)

            if len(validations) > 0:
                break

            non_indices.add(index)

            index = (index + direction) % wrap

            if index == start_index and len(indices) == 0:
                yield None

                continue

        pos = bisect.bisect_left(indices, index, 0, len(indices))

        if pos >= len(indices) or indices[pos] != index:
            indices.insert(pos, index)

        yield CurationEntry(
            entries[index],
            validations,
            pos,
            "{}+".format(len(indices))
            if (len(indices) + len(non_indices)) < wrap
            else str(wrap),
        )


async def curate(registry, datamine, Controller, Formatter):
    click.echo("The data loaded was collected in the following environment:")
    echo_json(datamine.environment)

    provider_namespace = dict()

    for nid, namespace in registry.namespaces.items():
        for resource in namespace.resources:
            provider_namespace[resource.id] = namespace

    entries = curation_entries(
        datamine.providers,
        [lambda p: p.id in registry.resources, HTTPStatusError.check_and_create],
    )

    click.echo(click.style("Connecting to the curation controller ...", fg="yellow"))

    controller = CurationController.create(Controller)
    await controller.connect()

    formatter = controller.create_formatter(Formatter)

    click.echo(click.style("Starting curation process ...", fg="yellow"))

    next(entries)
    entry = entries.send(+1)

    while entry is not None:
        for validation in entry.validations:
            validation.format(formatter)

        namespace = provider_namespace[entry.entry.id]
        provider = registry.resources[entry.entry.id]

        navigation_url = "https://registry.identifiers.org/registry/{}".format(
            namespace.prefix
        )

        await controller.navigate(navigation_url)

        await formatter.output(
            navigation_url, provider, namespace, entry.position, entry.total
        )

        next(entries)

        entry = entries.send(await controller.prompt())

    await controller.disconnect()

    click.echo(click.style("No more entries left for curation.", fg="yellow"))
