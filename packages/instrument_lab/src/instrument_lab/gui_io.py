"""Dedicated Qt-thread VISA I/O worker for Instrument Lab GUI.

The VISA resource is created, used and destroyed exclusively on the worker
thread.  This avoids handing native VISA session objects between transient
QThreadPool workers or closing a session from the GUI thread while I/O is in
progress.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QObject, Signal, Slot

from instrument_core.transport import TransportConfig, VisaTransport


class InstrumentIOWorker(QObject):
    """Own one VISA session for the lifetime of a dedicated Qt thread."""

    connected = Signal(str, str, float)
    disconnected = Signal(str)
    query_finished = Signal(str, str, float)
    write_finished = Signal(str, float)
    operation_error = Signal(str, str)
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

        # Clear ownership first so a failing native close cannot leave the
        # Python side believing the session is still usable.
        self._transport = None
        self._resource = ""

        if transport is not None:
            transport.close()

        return resource

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
        except Exception as exc:
            self.operation_error.emit("query", str(exc))
            return

        self.query_finished.emit(command, response, elapsed_ms)

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
        except Exception as exc:
            self.operation_error.emit("write", str(exc))
            return

        self.write_finished.emit(command, elapsed_ms)

    @Slot()
    def shutdown(self) -> None:
        try:
            self._close_transport()
        except Exception:
            # Application shutdown must continue even if a vendor VISA close
            # routine reports an error.  The owning thread will terminate next.
            pass
        self.shutdown_finished.emit()
