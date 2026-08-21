"""Replay previously recorded instrument communication sessions."""

import base64
import json
from pathlib import Path

from instrument_core.errors import (
    ProtocolError,
)

from .base import (
    Transport,
    TransportConfig,
)


class ReplayMismatchError(
    ProtocolError
):
    """Replay command differs from the recorded session."""


class ReplayTransport(Transport):
    """
    Replay a RecordingTransport JSONL session.

    Drivers communicate with this class exactly as if they were
    communicating with a real instrument.
    """

    def __init__(
        self,
        session_path: str | Path,
    ):
        self.session_path = Path(
            session_path
        )

        if not self.session_path.exists():
            raise FileNotFoundError(
                self.session_path
            )

        events = []

        with self.session_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            for line in handle:
                line = line.strip()

                if not line:
                    continue

                events.append(
                    json.loads(line)
                )

        if not events:
            raise ValueError(
                "Replay session is empty"
            )

        header = events[0]

        if header.get("type") != "session":
            raise ValueError(
                "Replay session is missing "
                "the session header"
            )

        self.metadata = header

        super().__init__(
            TransportConfig(
                resource=(
                    "REPLAY::"
                    + str(
                        self.session_path
                    )
                ),
                timeout_ms=int(
                    header.get(
                        "timeout_ms",
                        5000,
                    )
                ),
            )
        )

        self._events = events[1:]
        self._index = 0
        self._open = False

    @property
    def is_open(self) -> bool:
        return self._open

    @property
    def remaining_events(
        self,
    ) -> int:
        return (
            len(self._events)
            - self._index
        )

    def _next_event(
        self,
        expected_type: str,
    ) -> dict:
        if self._index >= len(
            self._events
        ):
            raise ReplayMismatchError(
                "Replay session exhausted. "
                f"Expected event: "
                f"{expected_type}"
            )

        event = self._events[
            self._index
        ]

        self._index += 1

        actual_type = event.get(
            "type"
        )

        if actual_type != expected_type:
            raise ReplayMismatchError(
                "Replay event mismatch: "
                f"expected {expected_type}, "
                f"recorded {actual_type}, "
                f"event index "
                f"{self._index - 1}"
            )

        return event

    def open(self) -> None:
        self._next_event(
            "open"
        )

        self._open = True

    def close(self) -> None:
        self._next_event(
            "close"
        )

        self._open = False

    def write(
        self,
        command: str,
    ) -> None:
        event = self._next_event(
            "write"
        )

        recorded = event.get(
            "text",
            "",
        )

        if command != recorded:
            raise ReplayMismatchError(
                "SCPI command mismatch: "
                f"driver sent {command!r}, "
                f"session recorded "
                f"{recorded!r}"
            )

    def read(self) -> str:
        event = self._next_event(
            "read"
        )

        return str(
            event.get(
                "text",
                "",
            )
        )

    def write_raw(
        self,
        data: bytes,
    ) -> None:
        event = self._next_event(
            "write_raw"
        )

        recorded = base64.b64decode(
            event.get(
                "data",
                "",
            )
        )

        if data != recorded:
            raise ReplayMismatchError(
                "Raw write mismatch: "
                f"driver sent {len(data)} bytes, "
                f"session recorded "
                f"{len(recorded)} bytes"
            )

    def read_raw(self) -> bytes:
        event = self._next_event(
            "read_raw"
        )

        return base64.b64decode(
            event.get(
                "data",
                "",
            )
        )

    def clear(self) -> None:
        self._next_event(
            "clear"
        )

    def assert_complete(
        self,
    ) -> None:
        if self.remaining_events != 0:
            raise ReplayMismatchError(
                "Replay session was not fully "
                "consumed. Remaining events: "
                f"{self.remaining_events}"
            )
