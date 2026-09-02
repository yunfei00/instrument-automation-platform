"""Dedicated Qt-thread VISA I/O worker for Instrument Lab GUI.

The VISA resource is created, used and destroyed exclusively on the worker
thread. This avoids handing native VISA session objects between transient
QThreadPool workers or closing a session from the GUI thread while I/O is in
progress.

Binary catalog queries use the VISA IEEE 488.2 block reader instead of a raw
read-until-end operation. Any I/O timeout invalidates the current VISA session
so unread data cannot poison subsequent SCPI commands.

Higher-level instrument operations are executed on this same owner thread. This
lets an operation safely combine multiple SCPI writes/queries without moving the
native VISA session between threads.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QObject, Signal, Slot

from instrument_core.errors import InstrumentTimeoutError
from instrument_core.transport import TransportConfig, VisaTransport

from .operations import DEFAULT_OPERATION_REGISTRY


BINARY_QUERY_MIN_TIMEOUT_MS = 30000
BINARY_PREVIEW_BYTES = 32


def describe_binary_payload(data: bytes) -> str:
    """Return a compact summary of an IEEE block payload."""

    preview = data[:BINARY_PREVIEW_BYTES].hex(" ")

    return (
        "Binary response\n"
        "IEEE 488.2 definite-length block: yes\n"
        f"Payload bytes: {len(data)}\n"
        "Termination wait: disabled\n"
        f"First {min(len(data), BINARY_PREVIEW_BYTES)} payload bytes: {preview}"
    )


class InstrumentIOWorker(QObject):
    """Own one VISA session for the lifetime of a dedicated Qt thread."""

    connected = Signal(str, str, float)
    disconnected = Signal(str)
    query_finished = Signal(str, str, float)
    binary_query_finished = Signal(str, str, float)
    write_finished = Signal(str, float)
    instrument_operation_finished = Signal(str, object, float)
    operation_error = Signal(str, str)
    connection_lost = Signal(str, str)
    shutdown_finished = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._transport: VisaTransport | None = None
        self._resource = ""

    @property
    def is_connected(self) -> bool:
        return self._transport is not None

    def _close_transport(self) -> str:
        resource = self._resource
        transport = self._transport

        self._transport = None
        self._resource = ""

        if transport is not None:
            transport.close()

        return resource

    def _invalidate_after_timeout(
        self,
        operation: str,
        exc: InstrumentTimeoutError,
    ) -> None:
        resource = self._resource
        close_note = ""

        try:
            self._close_transport()
        except Exception as close_exc:
            close_note = f" Close also reported: {close_exc}"

        self.connection_lost.emit(
            operation,
            (
                f"{exc} Session {resource or '<unknown>'} was closed after "
                "the timeout to prevent unread/stale instrument data from "
                f"affecting later commands.{close_note} Reconnect before "
                "continuing."
            ),
        )

    @Slot(str, int, object)
    def connect_instrument(
        self,
        resource: str,
        timeout_ms: int,
        backend: object,
    ) -> None:
        if self._transport is not None:
            self.operation_error.emit(
                "connect",
                "An instrument session is already open.",
            )
            return

        transport = VisaTransport(
            TransportConfig(
                resource=resource,
                timeout_ms=timeout_ms,
            ),
            backend=backend if isinstance(backend, str) else None,
        )

        try:
            transport.open()
            started = time.perf_counter()
            idn = transport.query("*IDN?").strip()
            elapsed_ms = (time.perf_counter() - started) * 1000.0
        except Exception as exc:
            try:
                transport.close()
            except Exception:
                pass
            self.operation_error.emit("connect", str(exc))
            return

        self._transport = transport
        self._resource = resource
        self.connected.emit(resource, idn, elapsed_ms)

    @Slot(str)
    def disconnect_instrument(self, _reason: str = "") -> None:
        try:
            resource = self._close_transport()
        except Exception as exc:
            self.operation_error.emit("disconnect", str(exc))
            return

        self.disconnected.emit(resource)

    @Slot(str)
    def query(self, command: str) -> None:
        transport = self._transport
        if transport is None:
            self.operation_error.emit(
                "query",
                "Instrument is not connected.",
            )
            return

        try:
            started = time.perf_counter()
            response = transport.query(command).strip()
            elapsed_ms = (time.perf_counter() - started) * 1000.0
        except InstrumentTimeoutError as exc:
            self._invalidate_after_timeout("query", exc)
            return
        except Exception as exc:
            self.operation_error.emit("query", str(exc))
            return

        self.query_finished.emit(command, response, elapsed_ms)

    @Slot(str)
    def query_binary(self, command: str) -> None:
        """Read one IEEE 488.2 block using an extended temporary timeout."""

        transport = self._transport
        if transport is None:
            self.operation_error.emit(
                "binary query",
                "Instrument is not connected.",
            )
            return

        previous_timeout_ms = transport.config.timeout_ms
        binary_timeout_ms = max(
            previous_timeout_ms,
            BINARY_QUERY_MIN_TIMEOUT_MS,
        )

        try:
            if binary_timeout_ms != previous_timeout_ms:
                transport.set_timeout_ms(binary_timeout_ms)

            started = time.perf_counter()
            payload = transport.query_ieee_block_bytes(
                command,
                expect_termination=False,
            )
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            summary = describe_binary_payload(payload)

            if binary_timeout_ms != previous_timeout_ms:
                transport.set_timeout_ms(previous_timeout_ms)
        except InstrumentTimeoutError as exc:
            self._invalidate_after_timeout("binary query", exc)
            return
        except Exception as exc:
            try:
                if (
                    self._transport is not None
                    and binary_timeout_ms != previous_timeout_ms
                ):
                    transport.set_timeout_ms(previous_timeout_ms)
            except Exception:
                pass
            self.operation_error.emit("binary query", str(exc))
            return

        self.binary_query_finished.emit(
            command,
            summary,
            elapsed_ms,
        )

    @Slot(str)
    def write(self, command: str) -> None:
        transport = self._transport
        if transport is None:
            self.operation_error.emit(
                "write",
                "Instrument is not connected.",
            )
            return

        try:
            started = time.perf_counter()
            transport.write(command)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
        except InstrumentTimeoutError as exc:
            self._invalidate_after_timeout("write", exc)
            return
        except Exception as exc:
            self.operation_error.emit("write", str(exc))
            return

        self.write_finished.emit(command, elapsed_ms)

    @Slot(str, object)
    def run_instrument_operation(
        self,
        operation_id: str,
        parameters: object,
    ) -> None:
        """Execute one registered multi-command operation on this VISA thread."""

        transport = self._transport
        if transport is None:
            self.operation_error.emit(
                "instrument operation",
                "Instrument is not connected.",
            )
            return

        parameter_map = parameters if isinstance(parameters, dict) else {}

        try:
            started = time.perf_counter()
            result = DEFAULT_OPERATION_REGISTRY.run(
                operation_id,
                transport,
                parameter_map,
            )
            elapsed_ms = (time.perf_counter() - started) * 1000.0
        except InstrumentTimeoutError as exc:
            self._invalidate_after_timeout(
                f"operation:{operation_id}",
                exc,
            )
            return
        except Exception as exc:
            self.operation_error.emit(
                f"operation:{operation_id}",
                str(exc),
            )
            return

        self.instrument_operation_finished.emit(
            operation_id,
            result,
            elapsed_ms,
        )

        # Some composite helpers preserve partial results instead of re-raising
        # a transport exception. If they report a transport stop, invalidate the
        # session here so stale unread bytes cannot affect the next command.
        if isinstance(result, dict) and result.get("stop_reason") == "transport_error":
            resource = self._resource
            try:
                self._close_transport()
            except Exception:
                pass
            self.connection_lost.emit(
                f"operation:{operation_id}",
                (
                    "The operation reported a transport error. "
                    f"Session {resource or '<unknown>'} was closed; reconnect "
                    "before continuing."
                ),
            )

    @Slot()
    def shutdown(self) -> None:
        try:
            self._close_transport()
        except Exception:
            pass
        self.shutdown_finished.emit()
