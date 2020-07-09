import gzip
import json

from abc import ABC, abstractmethod

import click


class CurationSession(ABC):
    def __init__(
        self, filepath, position, visited,
    ):
        self.__filepath = filepath
        self.__position = position
        self.__visited = visited

        click.get_current_context().call_on_close(self.save)

    @abstractmethod
    def __len__(self):
        pass

    @property
    def position(self):
        return self.__position

    @property
    def visited(self):
        return self.__visited

    def update(self, position, visited):
        self.__position = position
        self.__visited = self.__visited.union(visited)

    @abstractmethod
    def serialise(self, position, visited):
        pass

    def save(self):
        if self.__filepath is not None:
            click.echo(
                click.style(
                    f"Saving the current curation session to {self.__filepath} ...",
                    fg="yellow",
                )
            )

            with gzip.open(self.__filepath, "wt") as file:
                json.dump(self.serialise(self.__position, self.__visited), file)
        else:
            click.echo(
                click.style(
                    f"The current curation session has been discarded.", fg="yellow"
                )
            )
