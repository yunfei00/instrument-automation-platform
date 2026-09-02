"""Qt instrument-specific control panels.

Panels are deliberately thin: they render instrument state and emit registered
Instrument Operation requests. They do not contain VISA ownership or direct
SCPI transport calls.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class DSOX3000Panel(QWidget):
    """First virtual front-panel surface for Keysight DSO-X 3000 scopes."""

    operation_requested = Signal(str, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._last_screenshot_data = b""
        self._last_screenshot_format = "PNG"
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        title = QLabel("Keysight DSO-X 3000 虚拟控制台")
        title.setStyleSheet("font-weight: 600; font-size: 16px;")
        root.addWidget(title)

        self.status_label = QLabel(
            "连接仪表后可读取当前状态。所有操作通过 Driver / Operation 层执行。"
        )
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        action_row = QHBoxLayout()
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["1", "2", "3", "4"])
        action_row.addWidget(QLabel("Channel"))
        action_row.addWidget(self.channel_combo)

        refresh_button = QPushButton("读取当前状态")
        refresh_button.clicked.connect(self._read_state)
        action_row.addWidget(refresh_button)

        single_button = QPushButton("Single")
        single_button.clicked.connect(
            lambda: self._emit("keysight.dsox3000.single", {})
        )
        action_row.addWidget(single_button)

        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(
            lambda: self._emit("keysight.dsox3000.stop", {})
        )
        action_row.addWidget(stop_button)

        screenshot_button = QPushButton("Screenshot")
        screenshot_button.clicked.connect(self._screenshot)
        action_row.addWidget(screenshot_button)

        snapshot_button = QPushButton("Snapshot All")
        snapshot_button.clicked.connect(self._snapshot)
        action_row.addWidget(snapshot_button)
        action_row.addStretch(1)
        root.addLayout(action_row)

        settings_grid = QGridLayout()

        channel_group = QGroupBox("Channel")
        channel_layout = QFormLayout(channel_group)
        self.channel_display_label = QLabel("-")
        self.channel_scale_edit = QLineEdit()
        self.channel_scale_edit.setPlaceholderText("V/div")
        self.channel_offset_edit = QLineEdit()
        self.channel_offset_edit.setPlaceholderText("V")
        channel_apply = QPushButton("应用 Channel")
        channel_apply.clicked.connect(self._apply_channel)
        channel_layout.addRow("Display", self.channel_display_label)
        channel_layout.addRow("Scale (V/div)", self.channel_scale_edit)
        channel_layout.addRow("Offset (V)", self.channel_offset_edit)
        channel_layout.addRow(channel_apply)
        settings_grid.addWidget(channel_group, 0, 0)

        timebase_group = QGroupBox("Timebase")
        timebase_layout = QFormLayout(timebase_group)
        self.timebase_scale_edit = QLineEdit()
        self.timebase_scale_edit.setPlaceholderText("s/div")
        self.timebase_position_edit = QLineEdit()
        self.timebase_position_edit.setPlaceholderText("s")
        timebase_apply = QPushButton("应用 Timebase")
        timebase_apply.clicked.connect(self._apply_timebase)
        timebase_layout.addRow("Scale (s/div)", self.timebase_scale_edit)
        timebase_layout.addRow("Position (s)", self.timebase_position_edit)
        timebase_layout.addRow(timebase_apply)
        settings_grid.addWidget(timebase_group, 0, 1)

        trigger_group = QGroupBox("Trigger（当前只读）")
        trigger_layout = QFormLayout(trigger_group)
        self.trigger_mode_label = QLabel("-")
        self.trigger_sweep_label = QLabel("-")
        self.trigger_source_label = QLabel("-")
        self.trigger_level_label = QLabel("-")
        trigger_layout.addRow("Mode", self.trigger_mode_label)
        trigger_layout.addRow("Sweep", self.trigger_sweep_label)
        trigger_layout.addRow("Source", self.trigger_source_label)
        trigger_layout.addRow("Level", self.trigger_level_label)
        settings_grid.addWidget(trigger_group, 1, 0)

        acquisition_group = QGroupBox("Acquisition（当前只读）")
        acquisition_layout = QFormLayout(acquisition_group)
        self.acquisition_type_label = QLabel("-")
        self.acquisition_points_label = QLabel("-")
        self.sample_rate_label = QLabel("-")
        acquisition_layout.addRow("Type", self.acquisition_type_label)
        acquisition_layout.addRow("Points", self.acquisition_points_label)
        acquisition_layout.addRow("Sample Rate", self.sample_rate_label)
        settings_grid.addWidget(acquisition_group, 1, 1)

        root.addLayout(settings_grid)

        preview_group = QGroupBox("Instrument Screen")
        preview_layout = QVBoxLayout(preview_group)
        preview_note = QLabel(
            "显示真实仪表屏幕截图。PNG/BMP 数据由 :DISPlay:DATA? 的 "
            "IEEE 488.2 binary block 获取。"
        )
        preview_note.setWordWrap(True)
        preview_layout.addWidget(preview_note)

        self.screen_label = QLabel("尚未读取仪表截图。")
        self.screen_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screen_label.setMinimumSize(420, 220)
        self.screen_label.setStyleSheet(
            "QLabel { border: 1px solid #777; background: #111; color: #ddd; }"
        )
        preview_layout.addWidget(self.screen_label, 1)

        preview_actions = QHBoxLayout()
        refresh_screen_button = QPushButton("刷新截图")
        refresh_screen_button.clicked.connect(self._screenshot)
        preview_actions.addWidget(refresh_screen_button)

        self.save_screenshot_button = QPushButton("保存截图")
        self.save_screenshot_button.setEnabled(False)
        self.save_screenshot_button.clicked.connect(self._save_screenshot)
        preview_actions.addWidget(self.save_screenshot_button)
        preview_actions.addStretch(1)
        preview_layout.addLayout(preview_actions)
        root.addWidget(preview_group)

        snapshot_group = QGroupBox("Snapshot All")
        snapshot_layout = QVBoxLayout(snapshot_group)
        self.snapshot_summary = QLabel("尚未读取 Snapshot。")
        snapshot_layout.addWidget(self.snapshot_summary)

        self.snapshot_table = QTableWidget(0, 4)
        self.snapshot_table.setHorizontalHeaderLabels(
            ["Measurement", "Value", "Unit", "Status"]
        )
        self.snapshot_table.setAlternatingRowColors(True)
        self.snapshot_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        snapshot_layout.addWidget(self.snapshot_table)
        root.addWidget(snapshot_group, 1)

    def _emit(self, operation_id: str, parameters: dict[str, object]) -> None:
        self.status_label.setText(f"准备执行：{operation_id}")
        self.operation_requested.emit(operation_id, parameters)

    def _channel(self) -> str:
        return self.channel_combo.currentText()

    def _read_state(self) -> None:
        self._emit(
            "keysight.dsox3000.read_control_state",
            {"channel": self._channel()},
        )

    def _screenshot(self) -> None:
        self._emit(
            "keysight.dsox3000.screenshot",
            {"format": "PNG", "palette": "COLor"},
        )

    def _snapshot(self) -> None:
        self._emit(
            "keysight.dsox3000.snapshot_all",
            {"channel": self._channel()},
        )

    def _apply_channel(self) -> None:
        self._emit(
            "keysight.dsox3000.set_channel",
            {
                "channel": self._channel(),
                "scale_v_div": self.channel_scale_edit.text().strip(),
                "offset_v": self.channel_offset_edit.text().strip(),
            },
        )

    def _apply_timebase(self) -> None:
        self._emit(
            "keysight.dsox3000.set_timebase",
            {
                "scale_s_div": self.timebase_scale_edit.text().strip(),
                "position_s": self.timebase_position_edit.text().strip(),
            },
        )

    def _save_screenshot(self) -> None:
        if not self._last_screenshot_data:
            return

        suffix = ".png" if self._last_screenshot_format.upper() == "PNG" else ".bmp"
        path_text, _ = QFileDialog.getSaveFileName(
            self,
            "保存仪表截图",
            f"dsox_screen{suffix}",
            "PNG image (*.png);;BMP image (*.bmp);;All files (*)",
        )
        if not path_text:
            return

        Path(path_text).write_bytes(self._last_screenshot_data)
        self.status_label.setText(f"截图已保存：{path_text}")

    @staticmethod
    def _number(value: object, suffix: str = "") -> str:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        return f"{number:.9g}{suffix}"

    def handle_operation_result(
        self,
        operation_id: str,
        result: object,
        elapsed_ms: float,
    ) -> None:
        self.status_label.setText(
            f"完成：{operation_id}  ({elapsed_ms:.1f} ms)"
        )
        if not isinstance(result, dict):
            return

        kind = result.get("kind")
        if kind == "keysight_dsox3000_control_state":
            self._render_control_state(result)
        elif kind == "instrument_screenshot":
            self._render_screenshot(result)
        elif kind == "keysight_infiniivision_snapshot_all":
            self._render_snapshot(result)
        elif kind == "keysight_dsox3000_setting_applied":
            self.status_label.setText(
                f"设置已发送：{result.get('applied', {})}。建议读取当前状态确认。"
            )
        elif kind == "keysight_dsox3000_action":
            self.status_label.setText(
                f"{result.get('action', 'action')}: {result.get('status', '')}"
            )

    def _render_screenshot(self, result: dict[str, object]) -> None:
        data = result.get("data")
        if not isinstance(data, (bytes, bytearray)):
            self.status_label.setText("Screenshot operation did not return image bytes.")
            return

        payload = bytes(data)
        pixmap = QPixmap()
        if not pixmap.loadFromData(payload):
            self.status_label.setText(
                f"收到 {len(payload)} bytes，但 Qt 无法解析截图格式。"
            )
            return

        self._last_screenshot_data = payload
        self._last_screenshot_format = str(result.get("format", "PNG"))
        self.save_screenshot_button.setEnabled(True)

        scaled = pixmap.scaled(
            720,
            420,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.screen_label.setPixmap(scaled)
        restore_error = result.get("inksaver_restore_error")
        message = (
            f"Screenshot: {result.get('format')} / {result.get('palette')} / "
            f"{result.get('byte_count')} bytes"
        )
        if restore_error:
            message += f" | INKSaver restore warning: {restore_error}"
        self.status_label.setText(message)

    def _render_control_state(self, result: dict[str, object]) -> None:
        channel = str(result.get("channel", self._channel()))
        index = self.channel_combo.findText(channel)
        if index >= 0:
            self.channel_combo.setCurrentIndex(index)

        self.channel_display_label.setText(
            "ON" if bool(result.get("channel_display")) else "OFF"
        )
        self.channel_scale_edit.setText(
            self._number(result.get("channel_scale_v_div"))
        )
        self.channel_offset_edit.setText(
            self._number(result.get("channel_offset_v"))
        )
        self.timebase_scale_edit.setText(
            self._number(result.get("timebase_scale_s_div"))
        )
        self.timebase_position_edit.setText(
            self._number(result.get("timebase_position_s"))
        )
        self.trigger_mode_label.setText(str(result.get("trigger_mode", "-")))
        self.trigger_sweep_label.setText(str(result.get("trigger_sweep", "-")))
        self.trigger_source_label.setText(str(result.get("trigger_source", "-")))
        self.trigger_level_label.setText(
            self._number(result.get("trigger_level_v"), " V")
        )
        self.acquisition_type_label.setText(
            str(result.get("acquisition_type", "-"))
        )
        self.acquisition_points_label.setText(
            str(result.get("acquisition_points", "-"))
        )
        self.sample_rate_label.setText(
            self._number(result.get("sample_rate_sps"), " Sa/s")
        )

    def _render_snapshot(self, result: dict[str, object]) -> None:
        measurements = result.get("measurements")
        if not isinstance(measurements, dict):
            return

        self.snapshot_table.setRowCount(0)
        for entry in measurements.values():
            if not isinstance(entry, dict):
                continue
            row = self.snapshot_table.rowCount()
            self.snapshot_table.insertRow(row)
            valid = bool(entry.get("valid"))
            value = entry.get("value") if valid else entry.get("raw")
            cells = (
                str(entry.get("label", "")),
                self._number(value) if value is not None else "-",
                str(entry.get("unit", "")),
                "OK" if valid else "INVALID",
            )
            for column, text in enumerate(cells):
                self.snapshot_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(text),
                )

        self.snapshot_table.resizeColumnsToContents()
        self.snapshot_summary.setText(
            "Source: {source} | Success: {ok}/{total} | Complete: {complete}".format(
                source=result.get("source", "-"),
                ok=result.get("successful_measurements", 0),
                total=result.get("measurement_count", 0),
                complete=result.get("collection_complete", False),
            )
        )
