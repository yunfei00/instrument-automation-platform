"""Instrument-control shell layered on top of the stable engineering GUI.

The existing command browser remains the engineering/debug surface. This module
adds reusable Instrument Operations plus instrument-family control panels. The
visual layer never owns VISA sessions and does not duplicate SCPI command logic.
"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDockWidget,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .gui_dsox_controls import DSOX3000ControlPanel
from .gui_fsw import FSWControlPanel
from .gui_stable import StableInstrumentLabWindow
from .models import SafetyLevel
from .operations import DEFAULT_OPERATION_REGISTRY, InstrumentOperation
from .panels import DEFAULT_PANEL_REGISTRY


class InstrumentOperationRequests(QObject):
    run_requested = Signal(str, object)


def json_safe_operation_result(value: object) -> object:
    """Convert an operation result to compact JSON-safe diagnostic metadata.

    Binary payloads and large numeric arrays must stay available to the owning
    dedicated panel, but should not be expanded into the optional Raw JSON dock.
    """

    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"<{len(value)} bytes>"
    if isinstance(value, dict):
        if value.get("kind") == "rohde_schwarz_fsw_trace":
            compact = dict(value)
            frequencies = compact.get("frequencies_hz")
            levels = compact.get("levels_dbm")
            if isinstance(frequencies, (list, tuple)):
                compact["frequencies_hz"] = f"<{len(frequencies)} points>"
            if isinstance(levels, (list, tuple)):
                compact["levels_dbm"] = f"<{len(levels)} points>"
            value = compact
        return {
            str(key): json_safe_operation_result(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [json_safe_operation_result(item) for item in value]
    return value


class InstrumentControlWindow(StableInstrumentLabWindow):
    """Stable Instrument Lab plus reusable operations and dedicated panels."""

    def __init__(self, repo_root: str | Path | None = None) -> None:
        super().__init__(repo_root=repo_root)

        self.setWindowTitle("Instrument Automation Studio")
        self._operation_requests = InstrumentOperationRequests(self)
        self._operation_editors: dict[str, QWidget] = {}
        self._active_panel: QWidget | None = None

        self._operation_requests.run_requested.connect(
            self._io_worker.run_instrument_operation
        )
        self._io_worker.instrument_operation_finished.connect(
            self._instrument_operation_finished
        )

        self._build_workspace_pages()
        self._build_operation_dock()
        self.profile_combo.currentIndexChanged.connect(
            self._profile_context_changed
        )
        self._profile_context_changed()

    # ------------------------------------------------------------------
    # Large two-page workspace
    # ------------------------------------------------------------------

    def _build_workspace_pages(self) -> None:
        """Keep Connection global and split the dense body into two big pages."""

        central = self.centralWidget()
        root = central.layout() if central is not None else None
        if root is None:
            raise RuntimeError("Instrument Lab central layout is unavailable")

        generic_surface: QWidget | None = None
        for index in range(root.count()):
            item = root.itemAt(index)
            widget = item.widget()
            if isinstance(widget, QSplitter):
                generic_surface = widget
                break

        if generic_surface is None:
            raise RuntimeError("Instrument Lab generic command surface was not found")

        root.removeWidget(generic_surface)

        self.workspace_tabs = QTabWidget(central)
        self.workspace_tabs.setDocumentMode(True)

        generic_page = QWidget(self.workspace_tabs)
        generic_layout = QVBoxLayout(generic_page)
        generic_layout.setContentsMargins(0, 0, 0, 0)
        generic_layout.addWidget(generic_surface)
        self.workspace_tabs.addTab(generic_page, "通用命令")
        self.generic_commands_page = generic_page

        custom_page = QWidget(self.workspace_tabs)
        custom_layout = QVBoxLayout(custom_page)
        custom_layout.setContentsMargins(6, 6, 6, 6)
        self.panel_container = QWidget(custom_page)
        self.panel_layout = QVBoxLayout(self.panel_container)
        self.panel_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.addWidget(self.panel_container, 1)
        self.workspace_tabs.addTab(custom_page, "定制控制")
        self.custom_control_page = custom_page

        root.addWidget(self.workspace_tabs, 1)

    # ------------------------------------------------------------------
    # Instrument-family panel host
    # ------------------------------------------------------------------

    def _clear_instrument_panel(self) -> None:
        self._active_panel = None
        while self.panel_layout.count():
            item = self.panel_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _refresh_instrument_panel(self) -> None:
        self._clear_instrument_panel()

        if self.current_profile is None:
            self.panel_layout.addWidget(QLabel("未选择 Instrument Profile。"))
            return

        definition = DEFAULT_PANEL_REGISTRY.find_for_profile(
            self.current_profile.key
        )
        if definition is None:
            note = QLabel(
                "当前 Instrument Profile 还没有专用控制面板。\n"
                "请使用“通用命令”页面的 Command Browser / Raw SCPI。"
            )
            note.setWordWrap(True)
            self.panel_layout.addWidget(note)
            return

        if definition.panel_type == "dsox3000":
            panel = DSOX3000ControlPanel(self.panel_container)
        elif definition.panel_type == "fsw":
            panel = FSWControlPanel(self.panel_container)
        else:
            note = QLabel(
                f"Panel '{definition.panel_type}' 已注册，但当前 GUI 尚无对应渲染器。"
            )
            note.setWordWrap(True)
            self.panel_layout.addWidget(note)
            return

        panel.operation_requested.connect(self._run_panel_operation)
        self.panel_layout.addWidget(panel, 1)
        self._active_panel = panel

    def _run_panel_operation(
        self,
        operation_id: str,
        parameters: object,
    ) -> None:
        try:
            operation = DEFAULT_OPERATION_REGISTRY.get(operation_id)
        except KeyError as exc:
            QMessageBox.critical(self, "Unknown Operation", str(exc))
            return

        if self.current_profile is None or not operation.supports_profile(
            self.current_profile.key
        ):
            QMessageBox.warning(
                self,
                "Operation/Profile Mismatch",
                "当前仪表 Profile 不支持这个操作。",
            )
            return

        parameter_map = parameters if isinstance(parameters, dict) else {}
        self._dispatch_operation(operation, parameter_map, source="PANEL")

    # ------------------------------------------------------------------
    # Generic operation dock
    # ------------------------------------------------------------------

    def _build_operation_dock(self) -> None:
        dock = QDockWidget("仪表操作 / Instrument Operations", self)
        dock.setObjectName("instrument_operations_dock")

        container = QWidget()
        layout = QVBoxLayout(container)

        selection_group = QGroupBox("操作")
        selection_layout = QFormLayout(selection_group)

        self.operation_combo = QComboBox()
        self.operation_combo.currentIndexChanged.connect(
            self._operation_changed
        )
        selection_layout.addRow("Operation", self.operation_combo)

        self.operation_description = QLabel()
        self.operation_description.setWordWrap(True)
        selection_layout.addRow("说明", self.operation_description)
        layout.addWidget(selection_group)

        self.operation_parameters_group = QGroupBox("参数")
        self.operation_parameters_layout = QFormLayout(
            self.operation_parameters_group
        )
        layout.addWidget(self.operation_parameters_group)

        self.operation_run_button = QPushButton("执行操作")
        self.operation_run_button.clicked.connect(
            self._run_selected_operation
        )
        layout.addWidget(self.operation_run_button)

        self.operation_result_tabs = QTabWidget()

        self.operation_table = QTableWidget(0, 5)
        self.operation_table.setHorizontalHeaderLabels(
            ["Measurement", "Value", "Unit", "Status", "Command"]
        )
        self.operation_table.setAlternatingRowColors(True)
        self.operation_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.operation_result_tabs.addTab(self.operation_table, "Table")

        self.operation_result = QPlainTextEdit()
        self.operation_result.setReadOnly(True)
        self.operation_result.setPlaceholderText(
            "复合操作的原始结构化结果会显示在这里。"
        )
        self.operation_result_tabs.addTab(self.operation_result, "Raw JSON")
        layout.addWidget(self.operation_result_tabs, 1)

        dock.setWidget(container)
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea,
            dock,
        )
        self.operation_dock = dock

        # Keep both large workspace pages spacious by default. Advanced users
        # can reopen Instrument Operations from the View menu when needed.
        dock.hide()
        view_menu = self.menuBar().addMenu("视图")
        toggle_action = dock.toggleViewAction()
        toggle_action.setText("高级 Instrument Operations")
        view_menu.addAction(toggle_action)

    def _profile_context_changed(self, _index: int | None = None) -> None:
        self._refresh_operations()
        self._refresh_instrument_panel()

    def _current_operation(self) -> InstrumentOperation | None:
        operation_id = self.operation_combo.currentData()
        if not operation_id:
            return None
        try:
            return DEFAULT_OPERATION_REGISTRY.get(str(operation_id))
        except KeyError:
            return None

    def _refresh_operations(self, _index: int | None = None) -> None:
        self.operation_combo.blockSignals(True)
        self.operation_combo.clear()

        if self.current_profile is not None:
            operations = DEFAULT_OPERATION_REGISTRY.list_for_profile(
                self.current_profile.key
            )
            for operation in operations:
                self.operation_combo.addItem(
                    operation.title,
                    operation.id,
                )

        self.operation_combo.blockSignals(False)
        self._operation_changed()

    def _clear_operation_parameters(self) -> None:
        self._operation_editors.clear()
        while self.operation_parameters_layout.count():
            item = self.operation_parameters_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _operation_changed(self, _index: int | None = None) -> None:
        self._clear_operation_parameters()
        operation = self._current_operation()

        if operation is None:
            self.operation_description.setText(
                "当前 Instrument Profile 暂无已注册的高级操作。"
            )
            self.operation_run_button.setEnabled(False)
            return

        self.operation_description.setText(
            f"{operation.description}\nSafety: {operation.safety.value}"
        )

        for parameter in operation.parameters:
            if parameter.choices:
                editor = QComboBox()
                editor.addItems(list(parameter.choices))
                if parameter.default is not None:
                    default_text = str(parameter.default)
                    index = editor.findText(default_text)
                    if index >= 0:
                        editor.setCurrentIndex(index)
            else:
                editor = QLineEdit()
                if parameter.default is not None:
                    editor.setText(str(parameter.default))
                if parameter.description:
                    editor.setPlaceholderText(parameter.description)

            if parameter.description:
                editor.setToolTip(parameter.description)

            self._operation_editors[parameter.name] = editor
            self.operation_parameters_layout.addRow(
                parameter.label,
                editor,
            )

        self.operation_run_button.setEnabled(True)

    def _operation_parameters(self) -> dict[str, object]:
        values: dict[str, object] = {}
        operation = self._current_operation()
        if operation is None:
            return values

        parameter_map = {
            parameter.name: parameter
            for parameter in operation.parameters
        }

        for name, editor in self._operation_editors.items():
            if isinstance(editor, QComboBox):
                value: object = editor.currentText()
            elif isinstance(editor, QLineEdit):
                value = editor.text().strip()
            else:
                continue

            kind = parameter_map[name].kind
            if kind == "int" and value != "":
                value = int(str(value))
            elif kind == "float" and value != "":
                value = float(str(value))

            values[name] = value

        return values

    def _confirm_operation(self, operation: InstrumentOperation) -> bool:
        if operation.safety == SafetyLevel.SAFE:
            return True

        answer = QMessageBox.warning(
            self,
            "Instrument Operation Safety",
            (
                f"Operation '{operation.title}' is marked "
                f"{operation.safety.value}.\n\n"
                "它可能改变仪表状态。是否继续？"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _run_selected_operation(self) -> None:
        operation = self._current_operation()
        if operation is None:
            return

        try:
            parameters = self._operation_parameters()
        except ValueError as exc:
            QMessageBox.warning(self, "Operation Parameters", str(exc))
            return

        self._dispatch_operation(operation, parameters, source="OPERATION")

    def _dispatch_operation(
        self,
        operation: InstrumentOperation,
        parameters: dict[str, object],
        *,
        source: str,
    ) -> None:
        if not self._ensure_connected() or self._busy:
            return
        if not self._confirm_operation(operation):
            return

        operation_name = f"operation:{operation.id}"
        if not self._begin_io(operation_name):
            return

        self._append_log(
            source,
            operation.id,
            json.dumps(parameters, ensure_ascii=False),
        )
        self.operation_result.setPlainText("执行中...")
        self.operation_table.setRowCount(0)
        self.operation_result_tabs.setCurrentWidget(self.operation_result)
        self._operation_requests.run_requested.emit(
            operation.id,
            parameters,
        )

    # ------------------------------------------------------------------
    # Result rendering
    # ------------------------------------------------------------------

    @staticmethod
    def _display_value(value: object) -> str:
        if value is None:
            return "-"
        if isinstance(value, float):
            return f"{value:.12g}"
        return str(value)

    def _render_snapshot_table(self, result: dict[str, object]) -> bool:
        if result.get("kind") != "keysight_infiniivision_snapshot_all":
            return False

        measurements = result.get("measurements")
        if not isinstance(measurements, dict):
            return False

        self.operation_table.setRowCount(0)
        for entry in measurements.values():
            if not isinstance(entry, dict):
                continue

            row = self.operation_table.rowCount()
            self.operation_table.insertRow(row)
            valid = bool(entry.get("valid"))
            value = entry.get("value") if valid else entry.get("raw")
            cells = (
                entry.get("label", ""),
                value,
                entry.get("unit", ""),
                "OK" if valid else "INVALID",
                entry.get("command", ""),
            )
            for column, value in enumerate(cells):
                self.operation_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(self._display_value(value)),
                )

        self.operation_table.resizeColumnsToContents()
        self.operation_result_tabs.setCurrentWidget(self.operation_table)
        return True

    def _instrument_operation_finished(
        self,
        operation_id: str,
        result: object,
        elapsed_ms: float,
    ) -> None:
        safe_result = json_safe_operation_result(result)
        try:
            rendered = json.dumps(
                safe_result,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        except TypeError:
            rendered = str(safe_result)

        self.operation_result.setPlainText(rendered)
        if isinstance(result, dict):
            if not self._render_snapshot_table(result):
                self.operation_result_tabs.setCurrentWidget(
                    self.operation_result
                )

        panel = self._active_panel
        if panel is not None and hasattr(panel, "handle_operation_result"):
            panel.handle_operation_result(
                operation_id,
                result,
                elapsed_ms,
            )

        self._append_log(
            "OPERATION RESULT",
            operation_id,
            f"{elapsed_ms:.1f} ms",
        )
        self._finish_io()


def run_gui(repo_root: str | Path | None = None) -> int:
    app = QApplication.instance() or QApplication([])
    window = InstrumentControlWindow(repo_root=repo_root)
    window.show()
    return app.exec()
