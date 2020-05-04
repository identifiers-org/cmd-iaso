from abc import ABC, abstractmethod
from collections import namedtuple, Counter

import click

from .utils import echo_json

from requests.status_codes import _codes as status_codes

import pyppeteer

from asyncio import Future

import pathlib

import json


def patch_pyppeteer():
    import pyppeteer.connection

    original_method = pyppeteer.connection.websockets.client.connect

    def new_method(*args, **kwargs):
        kwargs["ping_interval"] = None
        kwargs["ping_timeout"] = None
        return original_method(*args, **kwargs)

    pyppeteer.connection.websockets.client.connect = new_method


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
                await self.page.addStyleTag(
                    content="""
                    #iaso-header {
                        display: none;
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
                        display: block;
                        width: 100%;
                        height: 100%;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background-color: rgba(0, 0, 0, 0.75);
                        z-index: 10;
                    }
                    
                    #iaso-overlay-content {
                        max-height: 100%;
                        overflow-y: scroll;
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
                    const overlay = document.createElement('div');
                    overlay.id = "iaso-overlay";
                    
                    overlay.innerHTML = `
                        <div id="iaso-overlay-content">
                            <h3 style="color: orange">Curation required for resource provider <span id="iaso-overlay-provider" style="font-weight: bold"></span>:</h3>
                            <h4 style="color: white">The following issues were observed:</h4>
                            <ul id="iaso-overlay-issues"></ul>
                        </div>
                    `;
                    
                    overlay.onclick = function () {
                        document.getElementById("iaso-overlay").style.display = 'none';
                        document.getElementById('iaso-header').style.display = 'block';
                    };
                    
                    document.body.insertBefore(overlay, document.body.firstElementChild);
                
                    const header = document.createElement('div');
                    header.id = "iaso-header";
                    
                    header.innerHTML = `
                        <button class="iaso-button" onclick="document.getElementById('iaso-overlay').style.display = 'block'; document.getElementById('iaso-header').style.display = 'none';">Information</button>
                        <button class="iaso-button" onclick="console.info('iaso-fw')">Forward</button>
                        <button class="iaso-button" onclick="console.info('iaso-bw')">Backward</button>
                        <button class="iaso-button" onclick="console.info('iaso-end')">End Session</button>
                    `;
                    
                    document.body.insertBefore(header, document.body.firstElementChild);
                }"""
                )

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
            browserWSEndpoint=(await self.initiator())
        )
        self.page = await self.browser.newPage()

        await self.page.setViewport({"width": 0, "height": 0})

        self.page.on("framenavigated", onnavigate)
        self.page.on("close", onclose)
        self.page.on("console", onconsole)

    async def navigate(self, url):
        await self.page.goto(url)

        await self.page.setViewport({"width": 0, "height": 0})

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
    async def output(self, resource, namespace):
        pass


class TerminalFormatter(CurationFormatter):
    def __init__(self):
        self.buffer = []

    def format_json(self, title, content):
        self.buffer.append((title, content))

    async def output(self, resource, namespace):
        ctx = click.get_current_context()

        click.echo("=" * 80 if ctx.max_content_width is None else max_content_width)

        click.echo(
            "{}{}{}".format(
                click.style("Curation required for resource provider ", fg="yellow"),
                click.style(resource.name, fg="yellow", bold=True),
                click.style(":", fg="yellow"),
            )
        )
        click.echo(
            "  {}".format(
                click.style(
                    "https://registry.identifiers.org/registry/{}".format(
                        namespace.prefix
                    ),
                    fg="bright_blue",
                    underline=True,
                )
            )
        )

        click.echo("The following issues were observed:")

        for title, content in self.buffer:
            click.echo("- {}: ".format(click.style(title, underline=True)), nl=False)

            echo_json(content, indent=1)

        click.echo("=" * 80 if ctx.max_content_width is None else max_content_width)

        self.buffer.clear()


class PyppeteerFormatter(CurationFormatter):
    def __init__(self, page=None):
        self.page = page
        self.buffer = []

    def format_json(self, title, content):
        self.buffer.append((title, content))

    async def output(self, resource, namespace):
        if self.page is not None:
            await self.page.waitForSelector("#iaso-overlay")

            await self.page.evaluate(
                """{
                const overlay_provider = document.getElementById("iaso-overlay-provider");
                overlay_provider.innerHTML = '"""
                + resource.name
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


CurationEntry = namedtuple("CurationEntry", ("entry", "validations"))


def curation_entries(entries, validators):
    wrap = len(entries)
    index = 0

    found = False

    while True:
        direction = yield

        if direction != +1 and direction != -1:
            yield None

            continue

        start_index = index

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

            index = (index + direction) % wrap

            if index == start_index and not found:
                yield None

                continue

        found = True

        yield CurationEntry(entries[index], validations)

        index = (index + direction) % wrap


async def curate(registry, datamine, Controller, Formatter):
    provider_namespace = dict()

    for nid, namespace in registry.namespaces.items():
        for resource in namespace.resources:
            provider_namespace[resource.id] = namespace

    entries = curation_entries(
        datamine.providers,
        [lambda p: p.id in registry.resources, HTTPStatusError.check_and_create],
    )

    next(entries)
    entry = entries.send(+1)

    controller = CurationController.create(Controller)
    await controller.connect()

    formatter = controller.create_formatter(Formatter)

    while entry is not None:
        for validation in entry.validations:
            validation.format(formatter)

        namespace = provider_namespace[entry.entry.id]
        provider = registry.resources[entry.entry.id]

        await controller.navigate(
            "https://registry.identifiers.org/registry/{}".format(namespace.prefix)
        )
        await formatter.output(provider, namespace)

        next(entries)

        entry = entries.send(await controller.prompt())

    await controller.disconnect()

    click.echo(click.style("No more entries left for curation.", fg="yellow"))
