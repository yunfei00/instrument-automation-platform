"""Stability wrapper for Instrument Lab GUI.

The original GUI remains the visual implementation. This subclass replaces
its transient QThreadPool VISA execution with one persistent QThread whose
worker owns the native VISA session for its entire lifetime.

It also stores successful instrument addresses locally per profile so lab
users do not need to re-enter the same address on every launch.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QMetaObject,
    QObject,
    QSettings,
    QThread,
    Qt,
    Signal,
)
from PySide6.QtWidgets import QApplication, QMessageBox

from .gui import InstrumentLabWindow
from .gui_backend import normalize_visa_resource
from .gui_io import InstrumentIOWorker
from .models import ResponseType


class IORequests(QObject):
    connect_requested = Signal(str, int, object)
    disconnect_requested = Signal(str)
    query_requested = Signal(str)
    binary_query_requested = Signal(str)
    write_requested = Signal(str)


class StableInstrumentLabWindow(InstrumentLabWindow):
    """Instrument Lab window with strict VISA thread ownership."""

    SETTINGS_ORGANIZATION = "instrument-automation-platform"
    SETTINGS_APPLICATION = "InstrumentLab"

    def __init__(
        self,
        repo_root: str | Path | None = None,
    ) -> None:
        # QSettings is created before the base window loads profiles because
        # profile selection calls the overridden _profile_changed() method.
        self._settings = QSettings(
            self.SETTINGS_ORGANIZATION,
            self.SETTINGS_APPLICATION,
        )
        self._pending_profile_key = ""
        self._pending_address_text = ""

        super().__init__(repo_root=repo_root)

        self._io_connected = False
        self._pending_operation_name = ""

        self.address_edit.setToolTip(
            "The last successfully connected address is saved locally "
            "for each instrument profile."
        )

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
        self._io_requests.binary_query_requested.connect(
            self._io_worker.query_binary
        )
        self._io_requests.write_requested.connect(
            self._io_worker.write
        )

        self._io_worker.connected.connect(self._io_connected_result)
        self._io_worker.disconnected.connect(self._io_disconnected_result)
        self._io_worker.query_finished.connect(self._io_query_result)
        self._io_worker.binary_query_finished.connect(
            self._io_binary_query_result
        )
        self._io_worker.write_finished.connect(self._io_write_result)
        self._io_worker.operation_error.connect(self._io_error)
        self._io_worker.connection_lost.connect(
            self._io_connection_lost
        )

        self._io_thread.start()

    @staticmethod
    def _address_settings_key(profile_key: str) -> str:
        return f"profiles/{profile_key}/address"

    def _profile_changed(self, _index: int | None = None) -> None:
        """Load the locally remembered address for the selected profile."""

        super()._profile_changed(_index)

        if self.current_profile is None:
            self.address_edit.clear()
            return

        saved_address = self._settings.value(
            self._address_settings_key(self.current_profile.key),
            "",
            type=str,
        )
        self.address_edit.setText(saved_address)

    def _set_connection_inputs_enabled(self) -> None:
        editable = not self._io_connected and not self._busy
        self.profile_combo.setEnabled(editable)
        self.address_edit.setEnabled(editable)
        self.timeout_spin.setEnabled(editable)
        self.backend_edit.setEnabled(editable)

    def _begin_io(self, operation_name: str) -> bool:
        if self._busy:
            return False
        self._busy = True
        self._pending_operation_name = operation_name
        self._update_action_state()
        self._set_connection_inputs_enabled()
        return True

    def _finish_io(self) -> None:
        self._busy = False
        self._pending_operation_name = ""
        self._update_action_state()
        self._set_connection_inputs_enabled()

    def _connect_or_disconnect(self) -> None:
        if self._io_connected:
            self._disconnect_instrument()
        else:
            self._connect_instrument()

    def _connect_instrument(self) -> None:
        if self._busy or self._io_connected:
            return

        address_text = self.address_edit.text().strip()

        try:
            resource = normalize_visa_resource(address_text)
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

        self._pending_profile_key = (
            self.current_profile.key
            if self.current_profile is not None
            else ""
        )
        self._pending_address_text = address_text

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

        if self._pending_profile_key and self._pending_address_text:
            self._settings.setValue(
                self._address_settings_key(self._pending_profile_key),
                self._pending_address_text,
            )
            self._settings.sync()
            self._append_log(
                "ADDRESS SAVED",
                self._pending_profile_key,
                self._pending_address_text,
            )

        self._pending_profile_key = ""
        self._pending_address_text = ""

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

    def _selected_query_is_binary(self, label: str) -> bool:
        """Use catalog response metadata only for baseline Query actions."""

        return (
            label == "QUERY"
            and self.current_entry is not None
            and self.current_entry.command.response_type
            == ResponseType.BINARY
        )

    def _execute_query(
        self,
        command: str,
        label: str,
    ) -> None:
        if not self._ensure_connected() or self._busy:
            return

        is_binary = self._selected_query_is_binary(label)
        operation_name = (
            "binary query"
            if is_binary
            else label.lower()
        )

        if not self._begin_io(operation_name):
            return

        display_label = "BINARY QUERY" if is_binary else label
        self._append_log(display_label, command, "")

        if is_binary:
            self._io_requests.binary_query_requested.emit(command)
        else:
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

    def _io_binary_query_result(
        self,
        command: str,
        summary: str,
        elapsed_ms: float,
    ) -> None:
        self.last_response.setPlainText(summary)

        compact_summary = " | ".join(
            line.strip()
            for line in summary.splitlines()
            if line.strip()
        )
        self._append_log(
            "BINARY RESPONSE",
            command,
            f"{compact_summary}  ({elapsed_ms:.1f} ms)",
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

    def _io_connection_lost(
        self,
        worker_operation: str,
        message: str,
    ) -> None:
        """A timeout closes the session so stale unread data cannot survive."""

        operation_name = (
            self._pending_operation_name
            or worker_operation
        )

        self._io_connected = False
        self.connected_resource = ""
        self.idn_label.clear()
        self._set_connected_state(False)

        self.last_response.setPlainText(
            f"TIMEOUT / SESSION CLOSED: {message}"
        )
        self._append_log(
            "SESSION CLOSED",
            operation_name,
            message,
        )
        self._finish_io()

        QMessageBox.warning(
            self,
            "Instrument Session Reset",
            "The command timed out. The VISA session was closed so unread "
            "response data cannot affect later commands.\n\nReconnect to "
            f"continue.\n\n{message}",
        )

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
            self._pending_profile_key = ""
            self._pending_address_text = ""
            self._set_connected_state(False)

        if worker_operation == "disconnect":
            # If close failed, do not allow the old session to be reused. The
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
        # Never close a native VISA session from the GUI thread. A blocking
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
