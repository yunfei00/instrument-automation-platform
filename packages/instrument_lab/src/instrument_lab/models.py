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


class VerificationStatus(str, Enum):
    CANDIDATE = "candidate"
    MANUAL_VERIFIED = "manual_verified"
    HARDWARE_VERIFIED = "hardware_verified"


@dataclass(frozen=True, slots=True)
class CommandDefinition:
    id: str
    name: str
    category: str
    command: str

    kind: CommandKind = CommandKind.QUERY
    safety: SafetyLevel = SafetyLevel.SAFE
    response_type: ResponseType = ResponseType.STRING

    set_command: str | None = None
    query_command: str | None = None

    unit: str | None = None

    description: str = ""
    response_notes: str = ""
    notes: str = ""

    source: str = ""
    manual_id: str = ""
    manual_page: int | None = None
    manual_section: str = ""

    verification_status: VerificationStatus = (
        VerificationStatus.CANDIDATE
    )

    probe_enabled: bool = True

    supported_models: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    @property
    def probe_command(self) -> str:
        if self.query_command:
            return self.query_command
        return self.command


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

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
