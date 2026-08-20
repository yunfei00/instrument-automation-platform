"""Common instrument data models."""

from dataclasses import dataclass
from enum import Enum


class InstrumentState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    READY = "ready"
    BUSY = "busy"
    RECOVERING = "recovering"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class InstrumentIdentity:
    manufacturer: str
    model: str
    serial_number: str = ""
    firmware: str = ""
    raw: str = ""

    @property
    def display_name(self) -> str:
        if self.manufacturer:
            return f"{self.manufacturer} {self.model}".strip()
        return self.model
