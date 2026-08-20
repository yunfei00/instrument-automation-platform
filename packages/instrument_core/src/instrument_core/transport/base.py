"""Transport abstraction used by all instrument drivers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class TransportConfig:
    resource: str
    timeout_ms: int = 5000
    read_termination: Optional[str] = "\n"
    write_termination: Optional[str] = "\n"


class Transport(ABC):
    """Vendor-independent instrument communication interface."""

    def __init__(self, config: TransportConfig):
        self.config = config

    @property
    @abstractmethod
    def is_open(self) -> bool:
        """Return True when the transport session is active."""

    @abstractmethod
    def open(self) -> None:
        """Open the connection."""

    @abstractmethod
    def close(self) -> None:
        """Close the connection."""

    @abstractmethod
    def write(self, command: str) -> None:
        """Send a text command."""

    @abstractmethod
    def read(self) -> str:
        """Read a text response."""

    def query(self, command: str) -> str:
        """Write a command and read its response."""
        self.write(command)
        return self.read()

    @abstractmethod
    def write_raw(self, data: bytes) -> None:
        """Send raw bytes."""

    @abstractmethod
    def read_raw(self) -> bytes:
        """Read raw bytes."""

    def query_raw(self, command: str) -> bytes:
        """Write a text command and return raw bytes."""
        self.write(command)
        return self.read_raw()

    @abstractmethod
    def clear(self) -> None:
        """Clear transport/instrument I/O buffers."""
