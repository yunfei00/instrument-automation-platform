"""Transport recording for reproducible instrument sessions."""

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from .base import Transport


SCHEMA_VERSION = "1"


def _utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


class RecordingTransport(Transport):
    """
    Transport decorator that records instrument communication.

    It wraps another Transport implementation such as VisaTransport
    and writes a JSON Lines session file.

    The driver does not know that recording is enabled.
    """

    def __init__(
        self,
        wrapped: Transport,
        session_path: str | Path,
        *,
        overwrite: bool = True,
    ):
        super().__init__(
            wrapped.config
        )

        self.wrapped = wrapped
        self.session_path = Path(
            session_path
        )

        self.session_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if (
            self.session_path.exists()
            and not overwrite
        ):
            raise FileExistsError(
                self.session_path
            )

        self._sequence = 0

        self.session_path.write_text(
            "",
            encoding="utf-8",
        )

        self._write_event(
            {
                "type": "session",
                "schema_version": SCHEMA_VERSION,
                "created_at": _utc_now(),
                "resource": (
                    wrapped.config.resource
                ),
                "timeout_ms": (
                    wrapped.config.timeout_ms
                ),
                "transport_class": (
                    type(wrapped).__name__
                ),
            }
        )

    @property
    def is_open(self) -> bool:
        return self.wrapped.is_open

    def _write_event(
        self,
        payload: dict,
    ) -> None:
        payload = dict(payload)

        payload["sequence"] = (
            self._sequence
        )

        self._sequence += 1

        with self.session_path.open(
            "a",
            encoding="utf-8",
        ) as handle:
            handle.write(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )

    def open(self) -> None:
        started = perf_counter()

        self.wrapped.open()

        elapsed_ms = (
            perf_counter() - started
        ) * 1000.0

        self._write_event(
            {
                "type": "open",
                "timestamp": _utc_now(),
                "elapsed_ms": round(
                    elapsed_ms,
                    3,
                ),
            }
        )

    def close(self) -> None:
        started = perf_counter()

        try:
            self.wrapped.close()
        finally:
            elapsed_ms = (
                perf_counter() - started
            ) * 1000.0

            self._write_event(
                {
                    "type": "close",
                    "timestamp": _utc_now(),
                    "elapsed_ms": round(
                        elapsed_ms,
                        3,
                    ),
                }
            )

    def write(
        self,
        command: str,
    ) -> None:
        started = perf_counter()

        self.wrapped.write(
            command
        )

        elapsed_ms = (
            perf_counter() - started
        ) * 1000.0

        self._write_event(
            {
                "type": "write",
                "timestamp": _utc_now(),
                "text": command,
                "elapsed_ms": round(
                    elapsed_ms,
                    3,
                ),
            }
        )

    def read(self) -> str:
        started = perf_counter()

        response = (
            self.wrapped.read()
        )

        elapsed_ms = (
            perf_counter() - started
        ) * 1000.0

        self._write_event(
            {
                "type": "read",
                "timestamp": _utc_now(),
                "text": response,
                "elapsed_ms": round(
                    elapsed_ms,
                    3,
                ),
            }
        )

        return response

    def write_raw(
        self,
        data: bytes,
    ) -> None:
        started = perf_counter()

        self.wrapped.write_raw(
            data
        )

        elapsed_ms = (
            perf_counter() - started
        ) * 1000.0

        self._write_event(
            {
                "type": "write_raw",
                "timestamp": _utc_now(),
                "encoding": "base64",
                "data": base64.b64encode(
                    data
                ).decode("ascii"),
                "size": len(data),
                "elapsed_ms": round(
                    elapsed_ms,
                    3,
                ),
            }
        )

    def read_raw(self) -> bytes:
        started = perf_counter()

        data = (
            self.wrapped.read_raw()
        )

        elapsed_ms = (
            perf_counter() - started
        ) * 1000.0

        self._write_event(
            {
                "type": "read_raw",
                "timestamp": _utc_now(),
                "encoding": "base64",
                "data": base64.b64encode(
                    data
                ).decode("ascii"),
                "size": len(data),
                "elapsed_ms": round(
                    elapsed_ms,
                    3,
                ),
            }
        )

        return data

    def clear(self) -> None:
        started = perf_counter()

        self.wrapped.clear()

        elapsed_ms = (
            perf_counter() - started
        ) * 1000.0

        self._write_event(
            {
                "type": "clear",
                "timestamp": _utc_now(),
                "elapsed_ms": round(
                    elapsed_ms,
                    3,
                ),
            }
        )
