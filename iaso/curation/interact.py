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


class CurationFormatter(ABC):
    @staticmethod
    async def create(Formatter, *args, **kwargs):
        fmt = Formatter(*args, **kwargs)

        if isinstance(fmt, CoroutineType):
            fmt = await fmt

        return fmt

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    @abstractmethod
    def format_json(self, identifier, title, content, level):
        pass

    @abstractmethod
    async def output(self, url, title, description, position, total):
        pass
