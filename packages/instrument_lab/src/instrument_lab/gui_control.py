"""Instrument-control shell layered on top of the stable engineering GUI.

The existing command browser remains the engineering/debug surface. This module
adds a generic Instrument Operations dock for reusable multi-command actions.
Instrument-specific control panels can later plug into the same shell without
moving SCPI knowledge into Qt widgets.
"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
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
    QVBoxLayout,
    QWidget,
)

from .gui_stable import StableInstrumentLabWindow
from .models import SafetyLevel
from .operations import DEFAULT_OPERATION_REGISTRY, InstrumentOperation


class InstrumentOperationRequests(QObject):
    run_requested = Signal(str, object)


class InstrumentControlWindow(StableInstrumentLabWindow):
    """Stable Instrument Lab plus reusable instrument-level operations."""

    def __init__(self, repo_root: str | Path | None = None) -> None:
        super().__init__(repo_root=repo_root)

        self.setWindowTitle("Instrument Automation Studio")
        self._operation_requests = InstrumentOperationRequests(self)
        self._operation_editors: dict[str, QWidget] = {}

        self._operation_requests.run_requested.connect(
            self._io_worker.run_instrument_operation
        )
        self._io_worker.instrument_operation_finished.connect(
            self._instrument_operation_finished
        )

        self._build_operation_dock()
        self.profile_combo.currentIndexChanged.connect(
            self._refresh_operations
        )
        self._refresh_operations()

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

        self.operation_result = QPlainTextEdit()
        self.operation_result.setReadOnly(True)
        self.operation_result.setPlaceholderText(
            "复合操作结果会显示在这里。Snapshot All 会返回结构化测量结果。"
        )
        layout.addWidget(self.operation_result, 1)

        dock.setWidget(container)
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea,
            dock,
        )
        self.operation_dock = dock

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
        if not self._ensure_connected() or self._busy:
            return
        if not self._confirm_operation(operation):
            return

        try:
            parameters = self._operation_parameters()
        except ValueError as exc:
            QMessageBox.warning(self, "Operation Parameters", str(exc))
            return

        operation_name = f"operation:{operation.id}"
        if not self._begin_io(operation_name):
            return

        self._append_log(
            "OPERATION",
            operation.id,
            json.dumps(parameters, ensure_ascii=False),
        )
        self.operation_result.setPlainText("执行中...")
        self._operation_requests.run_requested.emit(
            operation.id,
            parameters,
        )

    def _instrument_operation_finished(
        self,
        operation_id: str,
        result: object,
        elapsed_ms: float,
    ) -> None:
        try:
            rendered = json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        except TypeError:
            rendered = str(result)

        self.operation_result.setPlainText(rendered)
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
