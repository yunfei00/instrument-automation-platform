"""Stability wrapper for Instrument Lab GUI.

The original GUI remains the visual implementation.  This subclass replaces
its transient QThreadPool VISA execution with one persistent QThread whose
worker owns the native VISA session for its entire lifetime.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, QThread, Qt, Signal
from PySide6.QtWidgets import QApplication, QMessageBox

from .gui import InstrumentLabWindow
from .gui_backend import normalize_visa_resource
from .gui_io import InstrumentIOWorker


class IORequests(QObject):
    connect_requested = Signal(str, int, object)
    disconnect_requested = Signal(str)
    query_requested = Signal(str)
    write_requested = Signal(str)


class StableInstrumentLabWindow(InstrumentLabWindow):
    """Instrument Lab window with strict VISA thread ownership."""

    def __init__(
        self,
        repo_root: str | Path | None = None,
    ) -> None:
        super().__init__(repo_root=repo_root)

        self._io_connected = False
        self._pending_operation_name = ""

        self._io_thread = QThread(self)
        self._io_worker = InstrumentIOWorker()
        self._io_requests = IORequests(self)

        self._io_worker.moveToThread(self._io_thread)

        self._io_requests.connect_requested.connect(
            self._io_worker.connect_instrument
        )
        self._io_requests.disconnect_requested.connect(
            self._io_worker.disconnect_instrument
        )
        self._io_requests.query_requested.connect(
            self._io_worker.query
        )
        self._io_requests.write_requested.connect(
            self._io_worker.write
        )

        self._io_worker.connected.connect(self._io_connected_result)
        self._io_worker.disconnected.connect(self._io_disconnected_result)
        self._io_worker.query_finished.connect(self._io_query_result)
        self._io_worker.write_finished.connect(self._io_write_result)
        self._io_worker.operation_error.connect(self._io_error)

        self._io_thread.start()

    def _begin_io(self, operation_name: str) -> bool:
        if self._busy:
            return False
        self._busy = True
        self._pending_operation_name = operation_name
        self._update_action_state()
        return True

    def _finish_io(self) -> None:
        self._busy = False
        self._pending_operation_name = ""
        self._update_action_state()

    def _connect_or_disconnect(self) -> None:
        if self._io_connected:
            self._disconnect_instrument()
        else:
            self._connect_instrument()

    def _connect_instrument(self) -> None:
        if self._busy or self._io_connected:
            return

        try:
            resource = normalize_visa_resource(
                self.address_edit.text()
            )
        except ValueError as exc:
            QMessageBox.warning(
                self,
                "Invalid Address",
                str(exc),
            )
            return

        timeout_ms = self.timeout_spin.value()
        backend = self.backend_edit.text().strip() or None

        if not self._begin_io("connect"):
            return

        self._append_log("CONNECT", resource, "")
        self._io_requests.connect_requested.emit(
            resource,
            timeout_ms,
            backend,
        )

    def _io_connected_result(
        self,
        resource: str,
        idn: str,
        elapsed_ms: float,
    ) -> None:
        self._io_connected = True
        self.connected_resource = resource
        self.idn_label.setText(idn)
        self._set_connected_state(True)
        self._append_log(
            "RESPONSE",
            "*IDN?",
            f"{idn}  ({elapsed_ms:.1f} ms)",
        )
        self._finish_io()

    def _disconnect_instrument(self) -> None:
        if self._busy or not self._io_connected:
            return

        if not self._begin_io("disconnect"):
            return

        self._io_requests.disconnect_requested.emit("user")

    def _io_disconnected_result(self, resource: str) -> None:
        self._io_connected = False
        self.connected_resource = ""
        self.idn_label.clear()
        self._set_connected_state(False)
        self._append_log("DISCONNECT", resource, "")
        self._finish_io()

    def _ensure_connected(self) -> bool:
        if self._io_connected:
            return True

        QMessageBox.warning(
            self,
            "Not Connected",
            "Connect to an instrument before executing SCPI.",
        )
        return False

    def _execute_query(
        self,
        command: str,
        label: str,
    ) -> None:
        if not self._ensure_connected() or self._busy:
            return

        if not self._begin_io(label.lower()):
            return

        self._append_log(label, command, "")
        self._io_requests.query_requested.emit(command)

    def _io_query_result(
        self,
        command: str,
        response: str,
        elapsed_ms: float,
    ) -> None:
        self.last_response.setPlainText(response)
        self._append_log(
            "RESPONSE",
            command,
            f"{response}  ({elapsed_ms:.1f} ms)",
        )
        self._finish_io()

    def _execute_write(
        self,
        command: str,
        label: str,
    ) -> None:
        if not self._ensure_connected() or self._busy:
            return

        if not self._begin_io(label.lower()):
            return

        self._append_log(label, command, "")
        self._io_requests.write_requested.emit(command)

    def _io_write_result(
        self,
        command: str,
        elapsed_ms: float,
    ) -> None:
        self.last_response.setPlainText(
            f"WRITE OK ({elapsed_ms:.1f} ms)"
        )
        self._append_log(
            "WRITE OK",
            command,
            f"{elapsed_ms:.1f} ms",
        )
        self._finish_io()

    def _io_error(
        self,
        worker_operation: str,
        message: str,
    ) -> None:
        operation_name = (
            self._pending_operation_name
            or worker_operation
        )

        if worker_operation == "connect":
            self._io_connected = False
            self.connected_resource = ""
            self._set_connected_state(False)

        if worker_operation == "disconnect":
            # If close failed, do not allow the old session to be reused.  The
            # worker cleared ownership before attempting native close.
            self._io_connected = False
            self.connected_resource = ""
            self.idn_label.clear()
            self._set_connected_state(False)

        self.last_response.setPlainText(
            f"ERROR: {message}"
        )
        self._append_log(
            "ERROR",
            operation_name,
            message,
        )
        self._finish_io()

        QMessageBox.critical(
            self,
            "Instrument Operation Failed",
            message,
        )

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API name.
        # Never close a native VISA session from the GUI thread.  A blocking
        # queued call waits for any in-flight command to finish and then closes
        # the session on its owning worker thread.
        if self._io_thread.isRunning():
            try:
                QMetaObject.invokeMethod(
                    self._io_worker,
                    "shutdown",
                    Qt.ConnectionType.BlockingQueuedConnection,
                )
            except Exception:
                pass

            self._io_thread.quit()
            self._io_thread.wait()

        event.accept()


def run_gui(
    repo_root: str | Path | None = None,
) -> int:
    app = QApplication.instance() or QApplication([])
    window = StableInstrumentLabWindow(repo_root=repo_root)
    window.show()
    return app.exec()
