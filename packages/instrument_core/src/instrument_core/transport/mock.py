"""In-memory transport for unit tests and driver development."""

from collections import deque

from .base import Transport, TransportConfig


class MockTransport(Transport):
    def __init__(self, config: TransportConfig | None = None):
        super().__init__(
            config or TransportConfig(resource="MOCK::INSTR")
        )
        self._open = False
        self.writes: list[str] = []
        self.raw_writes: list[bytes] = []
        self._responses: deque[str] = deque()
        self._raw_responses: deque[bytes] = deque()

    @property
    def is_open(self) -> bool:
        return self._open

    def open(self) -> None:
        self._open = True

    def close(self) -> None:
        self._open = False

    def queue_response(self, response: str) -> None:
        self._responses.append(response)

    def queue_raw_response(self, response: bytes) -> None:
        self._raw_responses.append(response)

    def write(self, command: str) -> None:
        self.writes.append(command)

    def read(self) -> str:
        if not self._responses:
            raise RuntimeError("MockTransport has no queued text response")
        return self._responses.popleft()

    def write_raw(self, data: bytes) -> None:
        self.raw_writes.append(data)

    def read_raw(self) -> bytes:
        if not self._raw_responses:
            raise RuntimeError("MockTransport has no queued raw response")
        return self._raw_responses.popleft()

    def clear(self) -> None:
        self._responses.clear()
        self._raw_responses.clear()
