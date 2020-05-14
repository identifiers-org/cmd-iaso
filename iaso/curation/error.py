from abc import ABC, abstractmethod


class CurationError(ABC):
    @staticmethod
    @abstractmethod
    def check_and_create(provider):
        pass

    @abstractmethod
    def format(self, formatter):
        pass
