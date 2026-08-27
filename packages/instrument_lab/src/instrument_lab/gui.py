"""PySide6 engineering GUI for Instrument Lab."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import time
from typing import Callable

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from instrument_core.transport import TransportConfig, VisaTransport

from .gui_backend import (
    InstrumentCommandEntry,
    InstrumentProfile,
    discover_instrument_profiles,
    find_repo_root,
    normalize_visa_resource,
    save_candidate_command,
)
from .models import SafetyLevel


class WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str)
    finished = Signal()


class FunctionWorker(QRunnable):
    """Run one blocking function outside the Qt event loop."""

    def __init__(self, function: Callable[[], object]):
        super().__init__()
        self.function = function
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            result = self.function()
        except Exception as exc:  # GUI boundary: display any transport error.
            self.signals.error.emit(str(exc))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class CandidateCommandDialog(QDialog):
    """Collect metadata for an unverified command candidate."""

    def __init__(
        self,
        command_text: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Save Candidate Command")
        self.resize(560, 360)

        layout = QFormLayout(self)

        self.id_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.category_edit = QLineEdit("general")
        self.command_edit = QLineEdit(command_text)

        self.kind_combo = QComboBox()
        self.kind_combo.addItems(["query", "set", "action"])
        if command_text.strip().endswith("?"):
            self.kind_combo.setCurrentText("query")
        else:
            self.kind_combo.setCurrentText("set")

        self.response_combo = QComboBox()
        self.response_combo.addItems(
            [
                "string",
                "integer",
                "float",
                "boolean",
                "csv",
                "raw",
                "binary",
            ]
        )

        self.safety_combo = QComboBox()
        self.safety_combo.addItems(
            ["disruptive", "safe", "destructive"]
        )

        self.unit_edit = QLineEdit()
        self.description_edit = QPlainTextEdit()
        self.description_edit.setMaximumHeight(90)

        layout.addRow("Command ID", self.id_edit)
        layout.addRow("Name", self.name_edit)
        layout.addRow("Category", self.category_edit)
        layout.addRow("SCPI", self.command_edit)
        layout.addRow("Kind", self.kind_combo)
        layout.addRow("Response type", self.response_combo)
        layout.addRow("Safety", self.safety_combo)
        layout.addRow("Unit", self.unit_edit)
        layout.addRow("Description", self.description_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def values(self) -> dict[str, str]:
        return {
            "command_id": self.id_edit.text(),
            "name": self.name_edit.text(),
            "category": self.category_edit.text(),
            "command_text": self.command_edit.text(),
            "kind": self.kind_combo.currentText(),
            "response_type": self.response_combo.currentText(),
            "safety": self.safety_combo.currentText(),
            "unit": self.unit_edit.text(),
            "description": self.description_edit.toPlainText(),
        }


class InstrumentLabWindow(QMainWindow):
    """Generic command debugging workbench for supported instruments."""

    def __init__(
        self,
        repo_root: str | Path | None = None,
    ):
        super().__init__()
        self.repo_root = Path(
            repo_root or find_repo_root()
        ).resolve()

        self.profiles: list[InstrumentProfile] = []
        self.current_profile: InstrumentProfile | None = None
        self.current_entry: InstrumentCommandEntry | None = None
        self.transport: VisaTransport | None = None
        self.connected_resource = ""
        self._busy = False

        self.thread_pool = QThreadPool(self)
        # Serialize VISA operations for a single instrument session.
        self.thread_pool.setMaxThreadCount(1)

        self.setWindowTitle("Instrument Lab")
        self.resize(1320, 860)

        self._build_ui()
        self._load_profiles()
        self._set_connected_state(False)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        connection_group = QGroupBox("Instrument Connection")
        connection_layout = QGridLayout(connection_group)

        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(
            self._profile_changed
        )

        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText(
            "192.168.1.100 or TCPIP0::192.168.1.100::inst0::INSTR"
        )

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(100, 120000)
        self.timeout_spin.setValue(5000)
        self.timeout_spin.setSuffix(" ms")

        self.backend_edit = QLineEdit()
        self.backend_edit.setPlaceholderText(
            "optional VISA backend, e.g. @py"
        )

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(
            self._connect_or_disconnect
        )

        self.connection_status = QLabel("Disconnected")
        self.idn_label = QLabel("")
        self.idn_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        connection_layout.addWidget(QLabel("Instrument"), 0, 0)
        connection_layout.addWidget(self.profile_combo, 0, 1)
        connection_layout.addWidget(QLabel("Address"), 0, 2)
        connection_layout.addWidget(self.address_edit, 0, 3)
        connection_layout.addWidget(self.connect_button, 0, 4)
        connection_layout.addWidget(QLabel("Timeout"), 1, 0)
        connection_layout.addWidget(self.timeout_spin, 1, 1)
        connection_layout.addWidget(QLabel("VISA backend"), 1, 2)
        connection_layout.addWidget(self.backend_edit, 1, 3)
        connection_layout.addWidget(self.connection_status, 1, 4)
        connection_layout.addWidget(QLabel("*IDN?"), 2, 0)
        connection_layout.addWidget(self.idn_label, 2, 1, 1, 4)

        root.addWidget(connection_group)

        main_splitter = QSplitter(Qt.Horizontal)
        root.addWidget(main_splitter, 1)

        browser_widget = QWidget()
        browser_layout = QVBoxLayout(browser_widget)
        browser_layout.setContentsMargins(0, 0, 0, 0)

        self.profile_summary = QLabel()
        browser_layout.addWidget(self.profile_summary)

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText(
            "Filter by name, id, category or SCPI"
        )
        self.filter_edit.textChanged.connect(
            self._populate_command_tree
        )
        browser_layout.addWidget(self.filter_edit)

        self.command_tree = QTreeWidget()
        self.command_tree.setHeaderLabels(
            ["Command", "ID", "Safety", "Verification"]
        )
        self.command_tree.setAlternatingRowColors(True)
        self.command_tree.itemSelectionChanged.connect(
            self._command_selected
        )
        self.command_tree.setColumnWidth(0, 260)
        self.command_tree.setColumnWidth(1, 230)
        browser_layout.addWidget(self.command_tree, 1)

        main_splitter.addWidget(browser_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(6, 0, 0, 0)

        command_group = QGroupBox("Baseline Command")
        command_layout = QGridLayout(command_group)

        self.command_title = QLabel("Select a command")
        title_font = QFont()
        title_font.setBold(True)
        self.command_title.setFont(title_font)

        self.command_meta = QLabel("")
        self.command_meta.setWordWrap(True)
        self.command_description = QPlainTextEdit()
        self.command_description.setReadOnly(True)
        self.command_description.setMaximumHeight(100)

        self.query_edit = QLineEdit()
        self.query_edit.setPlaceholderText(
            "Query command; replace placeholders before execution"
        )
        self.query_button = QPushButton("Query")
        self.query_button.clicked.connect(
            self._query_baseline_command
        )

        self.send_edit = QLineEdit()
        self.send_edit.setPlaceholderText(
            "Set/action command; replace placeholders before execution"
        )
        self.send_button = QPushButton("Write")
        self.send_button.clicked.connect(
            self._write_baseline_command
        )

        command_layout.addWidget(self.command_title, 0, 0, 1, 3)
        command_layout.addWidget(self.command_meta, 1, 0, 1, 3)
        command_layout.addWidget(self.command_description, 2, 0, 1, 3)
        command_layout.addWidget(QLabel("Query"), 3, 0)
        command_layout.addWidget(self.query_edit, 3, 1)
        command_layout.addWidget(self.query_button, 3, 2)
        command_layout.addWidget(QLabel("Set/Action"), 4, 0)
        command_layout.addWidget(self.send_edit, 4, 1)
        command_layout.addWidget(self.send_button, 4, 2)

        right_layout.addWidget(command_group)

        raw_group = QGroupBox(
            "Raw SCPI Console - unrestricted engineering access"
        )
        raw_layout = QGridLayout(raw_group)

        self.raw_edit = QLineEdit()
        self.raw_edit.setPlaceholderText(
            "Enter any SCPI command, including commands not yet in the baseline"
        )
        self.raw_edit.returnPressed.connect(
            self._raw_query
        )

        self.raw_query_button = QPushButton("Query")
        self.raw_query_button.clicked.connect(self._raw_query)
        self.raw_write_button = QPushButton("Write")
        self.raw_write_button.clicked.connect(self._raw_write)
        self.save_candidate_button = QPushButton("Save Candidate")
        self.save_candidate_button.clicked.connect(
            self._save_candidate
        )

        self.last_response = QPlainTextEdit()
        self.last_response.setReadOnly(True)
        self.last_response.setMaximumHeight(120)

        raw_layout.addWidget(QLabel("SCPI"), 0, 0)
        raw_layout.addWidget(self.raw_edit, 0, 1)
        raw_layout.addWidget(self.raw_query_button, 0, 2)
        raw_layout.addWidget(self.raw_write_button, 0, 3)
        raw_layout.addWidget(self.save_candidate_button, 0, 4)
        raw_layout.addWidget(QLabel("Response"), 1, 0)
        raw_layout.addWidget(self.last_response, 1, 1, 1, 4)

        right_layout.addWidget(raw_group)

        log_group = QGroupBox("Session Log")
        log_layout = QVBoxLayout(log_group)
        self.log_edit = QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setLineWrapMode(
            QPlainTextEdit.NoWrap
        )
        clear_log_button = QPushButton("Clear Log")
        clear_log_button.clicked.connect(self.log_edit.clear)
        log_layout.addWidget(self.log_edit, 1)
        log_layout.addWidget(clear_log_button, 0, Qt.AlignRight)
        right_layout.addWidget(log_group, 1)

        main_splitter.addWidget(right_widget)
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 3)

    def _load_profiles(self, preserve_key: str = "") -> None:
        try:
            self.profiles = discover_instrument_profiles(
                self.repo_root
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Profile Discovery Failed",
                str(exc),
            )
            self.profiles = []

        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()

        selected_index = 0

        for index, profile in enumerate(self.profiles):
            manufacturer = profile.manufacturer or "Unknown"
            label = (
                f"{manufacturer} - {profile.display_name} "
                f"({profile.command_count} commands)"
            )
            self.profile_combo.addItem(label, profile.key)
            if preserve_key and profile.key == preserve_key:
                selected_index = index

        if self.profiles:
            self.profile_combo.setCurrentIndex(selected_index)

        self.profile_combo.blockSignals(False)
        self._profile_changed()

    def _profile_changed(self) -> None:
        index = self.profile_combo.currentIndex()

        if index < 0 or index >= len(self.profiles):
            self.current_profile = None
            self.profile_summary.setText("No instrument profiles found")
            self.command_tree.clear()
            return

        self.current_profile = self.profiles[index]
        profile = self.current_profile
        self.profile_summary.setText(
            f"Profile: {profile.key} | "
            f"Family: {profile.family or '-'} | "
            f"Commands: {profile.command_count} | "
            f"Categories: {len(profile.categories)}"
        )
        self.current_entry = None
        self._clear_command_detail()
        self._populate_command_tree()

    def _populate_command_tree(self) -> None:
        self.command_tree.clear()

        if self.current_profile is None:
            return

        filter_text = self.filter_edit.text().strip().lower()
        category_items: dict[str, QTreeWidgetItem] = {}

        for entry in self.current_profile.commands:
            command = entry.command
            haystack = " ".join(
                [
                    command.name,
                    command.id,
                    command.category,
                    command.command,
                    command.query_command or "",
                    command.set_command or "",
                ]
            ).lower()

            if filter_text and filter_text not in haystack:
                continue

            category_item = category_items.get(command.category)
            if category_item is None:
                category_item = QTreeWidgetItem(
                    [command.category, "", "", ""]
                )
                category_item.setFirstColumnSpanned(True)
                category_items[command.category] = category_item
                self.command_tree.addTopLevelItem(category_item)

            item = QTreeWidgetItem(
                [
                    command.name,
                    command.id,
                    command.safety.value,
                    command.verification_status.value,
                ]
            )
            item.setData(0, Qt.UserRole, entry)
            category_item.addChild(item)

        self.command_tree.expandAll()

    def _command_selected(self) -> None:
        items = self.command_tree.selectedItems()
        if not items:
            return

        entry = items[0].data(0, Qt.UserRole)
        if not isinstance(entry, InstrumentCommandEntry):
            return

        self.current_entry = entry
        command = entry.command

        self.command_title.setText(
            f"{command.name}  [{command.id}]"
        )

        relative_catalog = entry.catalog_path.relative_to(
            self.repo_root
        )
        self.command_meta.setText(
            f"Category: {command.category}   |   "
            f"Kind: {command.kind.value}   |   "
            f"Safety: {command.safety.value}   |   "
            f"Verification: {command.verification_status.value}   |   "
            f"Unit: {command.unit or '-'}\n"
            f"Catalog: {relative_catalog.as_posix()}"
        )

        description_parts = [command.description]
        if command.response_notes:
            description_parts.append(
                f"Response: {command.response_notes}"
            )
        if command.notes:
            description_parts.append(
                f"Notes: {command.notes}"
            )
        self.command_description.setPlainText(
            "\n".join(
                part
                for part in description_parts
                if part
            )
        )

        query_text = command.query_command or (
            command.command
            if command.command.strip().endswith("?")
            else ""
        )
        set_text = command.set_command or (
            command.command
            if command.kind.value in {"set", "action"}
            else ""
        )

        self.query_edit.setText(query_text)
        self.send_edit.setText(set_text)

    def _clear_command_detail(self) -> None:
        self.command_title.setText("Select a command")
        self.command_meta.clear()
        self.command_description.clear()
        self.query_edit.clear()
        self.send_edit.clear()

    def _connect_or_disconnect(self) -> None:
        if self.transport is None:
            self._connect_instrument()
        else:
            self._disconnect_instrument()

    def _connect_instrument(self) -> None:
        if self._busy:
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

        self._append_log("CONNECT", resource, "")

        def operation():
            transport = VisaTransport(
                TransportConfig(
                    resource=resource,
                    timeout_ms=timeout_ms,
                ),
                backend=backend,
            )
            try:
                transport.open()
                started = time.perf_counter()
                idn = transport.query("*IDN?").strip()
                elapsed_ms = (
                    time.perf_counter() - started
                ) * 1000.0
                return transport, resource, idn, elapsed_ms
            except Exception:
                transport.close()
                raise

        self._run_worker(
            operation,
            on_result=self._connected,
            operation_name="connect",
        )

    def _connected(self, result: object) -> None:
        transport, resource, idn, elapsed_ms = result
        self.transport = transport
        self.connected_resource = resource
        self.idn_label.setText(idn)
        self._set_connected_state(True)
        self._append_log(
            "RESPONSE",
            "*IDN?",
            f"{idn}  ({elapsed_ms:.1f} ms)",
        )

    def _disconnect_instrument(self) -> None:
        if self.transport is None or self._busy:
            return

        transport = self.transport
        resource = self.connected_resource

        def operation():
            transport.close()
            return resource

        def disconnected(result: object) -> None:
            self.transport = None
            self.connected_resource = ""
            self.idn_label.clear()
            self._set_connected_state(False)
            self._append_log("DISCONNECT", str(result), "")

        self._run_worker(
            operation,
            on_result=disconnected,
            operation_name="disconnect",
        )

    def _set_connected_state(self, connected: bool) -> None:
        self.connection_status.setText(
            "Connected" if connected else "Disconnected"
        )
        self.connect_button.setText(
            "Disconnect" if connected else "Connect"
        )
        self.profile_combo.setEnabled(not connected)
        self.address_edit.setEnabled(not connected)
        self.timeout_spin.setEnabled(not connected)
        self.backend_edit.setEnabled(not connected)

    def _confirm_catalog_safety(self) -> bool:
        if self.current_entry is None:
            return True

        safety = self.current_entry.command.safety
        if safety == SafetyLevel.SAFE:
            return True

        text = (
            f"This catalog command is marked {safety.value}.\n\n"
            "It may change instrument state. Continue?"
        )
        answer = QMessageBox.warning(
            self,
            "Instrument Command Safety",
            text,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return answer == QMessageBox.Yes

    @staticmethod
    def _has_unresolved_placeholders(command: str) -> bool:
        return "<" in command and ">" in command

    def _validate_executable_command(
        self,
        command: str,
    ) -> bool:
        if not command.strip():
            QMessageBox.warning(
                self,
                "Missing Command",
                "No SCPI command is available in this field.",
            )
            return False

        if self._has_unresolved_placeholders(command):
            QMessageBox.warning(
                self,
                "Unresolved Placeholder",
                "Replace placeholders such as <n> or <scale> before execution.",
            )
            return False

        return True

    def _query_baseline_command(self) -> None:
        command = self.query_edit.text().strip()
        if not self._validate_executable_command(command):
            return
        if not self._confirm_catalog_safety():
            return
        self._execute_query(command, "QUERY")

    def _write_baseline_command(self) -> None:
        command = self.send_edit.text().strip()
        if not self._validate_executable_command(command):
            return
        if not self._confirm_catalog_safety():
            return
        self._execute_write(command, "WRITE")

    def _raw_query(self) -> None:
        command = self.raw_edit.text().strip()
        if not self._validate_executable_command(command):
            return
        self._execute_query(command, "RAW QUERY")

    def _raw_write(self) -> None:
        command = self.raw_edit.text().strip()
        if not self._validate_executable_command(command):
            return
        self._execute_write(command, "RAW WRITE")

    def _require_transport(self) -> VisaTransport | None:
        if self.transport is None:
            QMessageBox.warning(
                self,
                "Not Connected",
                "Connect to an instrument before executing SCPI.",
            )
            return None
        return self.transport

    def _execute_query(
        self,
        command: str,
        label: str,
    ) -> None:
        transport = self._require_transport()
        if transport is None or self._busy:
            return

        self._append_log(label, command, "")

        def operation():
            started = time.perf_counter()
            response = transport.query(command).strip()
            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000.0
            return command, response, elapsed_ms

        def received(result: object) -> None:
            sent, response, elapsed_ms = result
            self.last_response.setPlainText(response)
            self._append_log(
                "RESPONSE",
                sent,
                f"{response}  ({elapsed_ms:.1f} ms)",
            )

        self._run_worker(
            operation,
            on_result=received,
            operation_name=label.lower(),
        )

    def _execute_write(
        self,
        command: str,
        label: str,
    ) -> None:
        transport = self._require_transport()
        if transport is None or self._busy:
            return

        self._append_log(label, command, "")

        def operation():
            started = time.perf_counter()
            transport.write(command)
            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000.0
            return command, elapsed_ms

        def written(result: object) -> None:
            sent, elapsed_ms = result
            self.last_response.setPlainText(
                f"WRITE OK ({elapsed_ms:.1f} ms)"
            )
            self._append_log(
                "WRITE OK",
                sent,
                f"{elapsed_ms:.1f} ms",
            )

        self._run_worker(
            operation,
            on_result=written,
            operation_name=label.lower(),
        )

    def _save_candidate(self) -> None:
        if self.current_profile is None:
            QMessageBox.warning(
                self,
                "No Profile",
                "Select an instrument profile first.",
            )
            return

        command_text = self.raw_edit.text().strip()
        if not command_text:
            QMessageBox.warning(
                self,
                "Missing Command",
                "Enter a raw SCPI command before saving a candidate.",
            )
            return

        dialog = CandidateCommandDialog(
            command_text,
            self,
        )
        if dialog.exec() != QDialog.Accepted:
            return

        profile_key = self.current_profile.key

        try:
            path = save_candidate_command(
                self.current_profile,
                **dialog.values(),
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Candidate Save Failed",
                str(exc),
            )
            return

        relative = path.relative_to(self.repo_root)
        self._append_log(
            "CANDIDATE",
            command_text,
            f"saved to {relative.as_posix()}",
        )
        QMessageBox.information(
            self,
            "Candidate Saved",
            "Saved as an unverified candidate.\n\n"
            f"{relative.as_posix()}\n\n"
            "verification_status = candidate\n"
            "probe_enabled = false",
        )
        self._load_profiles(preserve_key=profile_key)

    def _run_worker(
        self,
        operation: Callable[[], object],
        *,
        on_result: Callable[[object], None],
        operation_name: str,
    ) -> None:
        self._busy = True
        self._update_action_state()

        worker = FunctionWorker(operation)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(
            lambda message: self._worker_error(
                operation_name,
                message,
            )
        )
        worker.signals.finished.connect(
            self._worker_finished
        )
        self.thread_pool.start(worker)

    def _worker_error(
        self,
        operation_name: str,
        message: str,
    ) -> None:
        self.last_response.setPlainText(
            f"ERROR: {message}"
        )
        self._append_log(
            "ERROR",
            operation_name,
            message,
        )
        QMessageBox.critical(
            self,
            "Instrument Operation Failed",
            message,
        )

    def _worker_finished(self) -> None:
        self._busy = False
        self._update_action_state()

    def _update_action_state(self) -> None:
        enabled = not self._busy
        self.connect_button.setEnabled(enabled)
        self.query_button.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
        self.raw_query_button.setEnabled(enabled)
        self.raw_write_button.setEnabled(enabled)
        self.save_candidate_button.setEnabled(enabled)

    def _append_log(
        self,
        operation: str,
        command: str,
        detail: str,
    ) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"{timestamp}  {operation:<12}  {command}"
        if detail:
            line += f"  ->  {detail}"
        self.log_edit.appendPlainText(line)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API name.
        if self.transport is not None:
            try:
                self.transport.close()
            except Exception:
                pass
            self.transport = None
        event.accept()


def run_gui(
    repo_root: str | Path | None = None,
) -> int:
    app = QApplication.instance() or QApplication([])
    window = InstrumentLabWindow(repo_root=repo_root)
    window.show()
    return app.exec()
