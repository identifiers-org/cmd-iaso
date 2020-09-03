from ..institutions.academine import Academine
from ..json_schema_file import JsonSchemaFile
from ..jsondb import namedtuple_to_dict
from .session import CurationSession


class InstitutionsCurationSession(CurationSession):
    SCHEMA = {
        "type": "object",
        "properties": {
            "academine": Academine.SCHEMA,
            "position": {"type": "integer"},
            "visited": {
                "type": "array",
                "items": {"type": "integer", "minimum": 0},
                "additionalItems": False,
            },
        },
        "required": ["academine", "position", "visited"],
        "additionalProperties": False,
    }

    @staticmethod
    def load_from_file(filepath):
        session = JsonSchemaFile(
            filepath, "SESSION", InstitutionsCurationSession.SCHEMA
        )

        return InstitutionsCurationSession(
            filepath,
            session.academine,
            session.position,
            set(session.visited),
        )

    def __init__(
        self,
        filepath,
        academine,
        position,
        visited,
    ):
        super().__init__(filepath, position, visited)

        self.__academine = academine

    def __len__(self):
        return len(self.__academine.institutions)

    @property
    def academine(self):
        return self.__academine

    def serialise(self, position, visited):
        return {
            "academine": namedtuple_to_dict(self.__academine),
            "position": position,
            "visited": list(visited),
        }
