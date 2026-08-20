"""Data models used by Instrument Lab."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class CommandKind(str, Enum):
    QUERY = "query"
    SET = "set"
    ACTION = "action"


class SafetyLevel(str, Enum):
    SAFE = "safe"
    DISRUPTIVE = "disruptive"
    DESTRUCTIVE = "destructive"


class ResponseType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    CSV = "csv"
    RAW = "raw"
    BINARY = "binary"


@dataclass(frozen=True, slots=True)
class CommandDefinition:
    id: str
    name: str
    category: str
    command: str
    kind: CommandKind = CommandKind.QUERY
    safety: SafetyLevel = SafetyLevel.SAFE
    response_type: ResponseType = ResponseType.STRING
    unit: str | None = None
    description: str = ""
    notes: str = ""
    source: str = ""
    supported_models: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(slots=True)
class ProbeResult:
    command_id: str
    name: str
    command: str
    status: str
    raw_response: str | None = None
    parsed_value: Any = None
    parsed_type: str | None = None
    unit: str | None = None
    elapsed_ms: float | None = None
    error: str | None = None
    timestamp: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
