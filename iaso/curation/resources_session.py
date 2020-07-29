from ..datamine import Datamine
from ..json_schema_file import JsonSchemaFile
from ..jsondb import namedtuple_to_dict
from .session import CurationSession


class ResourcesCurationSession(CurationSession):
    SCHEMA = {
        "type": "object",
        "properties": {
            "datamine": Datamine.SCHEMA,
            "validators": {
                "type": "array",
                "items": {"type": "string"},
                "additionalItems": False,
            },
            "valid_luis_threshold": {"type": "integer", "minimum": 0, "maximum": 100},
            "random_luis_threshold": {"type": "integer", "minimum": 0, "maximum": 100},
            "position": {"type": "integer"},
            "visited": {
                "type": "array",
                "items": {"type": "integer", "minimum": 0},
                "additionalItems": False,
            },
        },
        "required": [
            "datamine",
            "validators",
            "valid_luis_threshold",
            "random_luis_threshold",
            "position",
            "visited",
        ],
        "additionalProperties": False,
    }

    @staticmethod
    def load_from_file(filepath, validate_validators):
        session = JsonSchemaFile(filepath, "SESSION", ResourcesCurationSession.SCHEMA)

        return ResourcesCurationSession(
            filepath,
            session.datamine,
            validate_validators(session.validators),
            session.valid_luis_threshold,
            session.random_luis_threshold,
            session.position,
            set(session.visited),
        )

    def __init__(
        self,
        filepath,
        datamine,
        validators,
        valid_luis_threshold,
        random_luis_threshold,
        position,
        visited,
    ):
        super().__init__(filepath, position, visited)

        self.__datamine = datamine
        self.__validators = validators
        self.__valid_luis_threshold = valid_luis_threshold
        self.__random_luis_threshold = random_luis_threshold

    def __len__(self):
        return len(self.__datamine.providers)

    @property
    def datamine(self):
        return self.__datamine

    @property
    def validators(self):
        return self.__validators

    @property
    def valid_luis_threshold(self):
        return self.__valid_luis_threshold

    @property
    def random_luis_threshold(self):
        return self.__random_luis_threshold

    def serialise(self, position, visited):
        return {
            "datamine": namedtuple_to_dict(self.__datamine),
            "validators": list(self.__validators.keys()),
            "valid_luis_threshold": self.__valid_luis_threshold,
            "random_luis_threshold": self.__random_luis_threshold,
            "position": position,
            "visited": list(visited),
        }
