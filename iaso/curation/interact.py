from abc import ABC, abstractmethod
from collections import OrderedDict
from threading import Thread
from types import CoroutineType

from .generator import CurationDirection


class CurationController(ABC):
    CHOICES = OrderedDict(
        rl=CurationDirection.RELOAD,
        fw=CurationDirection.FORWARD,
        bw=CurationDirection.BACKWARD,
        end=CurationDirection.FINISH,
    )

    @staticmethod
    async def create(Controller, *args, **kwargs):
        ctrl = Controller(*args, **kwargs)

        if isinstance(ctrl, CoroutineType):
            ctrl = await ctrl

        return ctrl

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    @abstractmethod
    async def prompt(self):
        pass


class CurationNavigator(ABC):
    @staticmethod
    async def create(Navigator, *args, **kwargs):
        nav = Navigator(*args, **kwargs)

        if isinstance(nav, CoroutineType):
            nav = await nav

        return nav

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    @abstractmethod
    async def navigate(self, url, auxiliary):
        pass


class CurationInformant(ABC):
    @staticmethod
    async def create(Informant, *args, **kwargs):
        fmt = Informant(*args, **kwargs)

        if isinstance(fmt, CoroutineType):
            fmt = await fmt

        return fmt

    def __init__(self, ignored_tags, tag_store):
        self.tag_store = tag_store

        self.ignored_tags = ignored_tags

        self.buffer = []
        self.tags_mapping = dict()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    def format_json(self, identifier, title, content, level):
        self.buffer.append((identifier, title, content, level))

    def check_if_non_empty_else_reset(self):
        for identifier, title, content, level in self.buffer:
            tags = self.tag_store.get_tags_for_identifier(identifier)

            if any(tag in self.ignored_tags for tag in tags):
                continue

            return True

        self.buffer.clear()

        return False

    @abstractmethod
    async def output(self, url, title, description, position, total):
        pass
