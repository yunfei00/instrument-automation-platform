"""Qt instrument-specific control panels.

Panels are deliberately thin: they render instrument state and emit registered
Instrument Operation requests. They do not contain VISA ownership or direct
SCPI transport calls.
"""

from __future__ import annotations

from bisect import bisect_left
import csv
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QPolygonF
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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .dsox_waveform_operation import ensure_dsox_waveform_operation_registered


ensure_dsox_waveform_operation_registered()


class WaveformPlotWidget(QWidget):
    """Lightweight Qt-only waveform renderer for engineering Data View.

    It intentionally avoids matplotlib/numpy so the desktop tool keeps the same
    small runtime dependency set. The full waveform stays in memory for export;
    only the visual polyline is decimated when a capture contains far more
    samples than horizontal screen pixels.
    """

    cursor_changed = Signal(int, float, float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._times: tuple[float, ...] = ()
        self._volts: tuple[float, ...] = ()
        self._cursor_index: int | None = None
        self.setMinimumSize(520, 280)
        self.setMouseTracking(True)

    def set_waveform(
        self,
        times: tuple[float, ...],
        volts: tuple[float, ...],
    ) -> None:
        if len(times) != len(volts):
            raise ValueError("Waveform time/voltage arrays must have equal length")
        self._times = times
        self._volts = volts
        self._cursor_index = None
        self.update()

    def clear_waveform(self) -> None:
        self._times = ()
        self._volts = ()
        self._cursor_index = None
        self.update()

    def _plot_rect(self) -> QRectF:
        return QRectF(58.0, 18.0, max(10.0, self.width() - 78.0), max(10.0, self.height() - 58.0))

    @staticmethod
    def _expanded_range(low: float, high: float) -> tuple[float, float]:
        if high > low:
            padding = (high - low) * 0.05
            return low - padding, high + padding
        padding = max(abs(low) * 0.05, 1e-12)
        return low - padding, high + padding

    def _ranges(self) -> tuple[float, float, float, float] | None:
        if not self._times or not self._volts:
            return None
        t_min, t_max = self._expanded_range(self._times[0], self._times[-1])
        v_min, v_max = self._expanded_range(min(self._volts), max(self._volts))
        return t_min, t_max, v_min, v_max

    @staticmethod
    def _map_point(
        time_s: float,
        voltage_v: float,
        rect: QRectF,
        ranges: tuple[float, float, float, float],
    ) -> QPointF:
        t_min, t_max, v_min, v_max = ranges
        x = rect.left() + (time_s - t_min) / (t_max - t_min) * rect.width()
        y = rect.bottom() - (voltage_v - v_min) / (v_max - v_min) * rect.height()
        return QPointF(x, y)

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(16, 18, 20))

        rect = self._plot_rect()
        painter.setPen(QPen(QColor(78, 82, 86), 1))
        for column in range(11):
            x = rect.left() + rect.width() * column / 10.0
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
        for row in range(9):
            y = rect.top() + rect.height() * row / 8.0
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))

        ranges = self._ranges()
        if ranges is None:
            painter.setPen(QColor(200, 200, 200))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "尚未读取波形数据")
            return

        t_min, t_max, v_min, v_max = ranges
        painter.setPen(QColor(190, 195, 200))
        painter.drawText(4, 28, f"{v_max:.6g} V")
        painter.drawText(4, int(rect.bottom()), f"{v_min:.6g} V")
        painter.drawText(int(rect.left()), self.height() - 12, f"{t_min:.6g} s")
        painter.drawText(int(rect.right() - 110), self.height() - 12, f"{t_max:.6g} s")

        max_visual_points = max(1000, int(rect.width() * 2.0))
        count = len(self._times)
        stride = max(1, count // max_visual_points)
        polygon = QPolygonF()
        for index in range(0, count, stride):
            polygon.append(
                self._map_point(
                    self._times[index],
                    self._volts[index],
                    rect,
                    ranges,
                )
            )
        if count > 1 and (count - 1) % stride:
            polygon.append(
                self._map_point(
                    self._times[-1],
                    self._volts[-1],
                    rect,
                    ranges,
                )
            )

        painter.setPen(QPen(QColor(255, 213, 64), 1.4))
        painter.drawPolyline(polygon)

        if self._cursor_index is not None and 0 <= self._cursor_index < count:
            point = self._map_point(
                self._times[self._cursor_index],
                self._volts[self._cursor_index],
                rect,
                ranges,
            )
            painter.setPen(QPen(QColor(90, 190, 255), 1))
            painter.drawLine(QPointF(point.x(), rect.top()), QPointF(point.x(), rect.bottom()))
            painter.drawLine(QPointF(rect.left(), point.y()), QPointF(rect.right(), point.y()))
            painter.setBrush(QColor(90, 190, 255))
            painter.drawEllipse(point, 3.0, 3.0)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt naming
        if not self._times:
            return
        rect = self._plot_rect()
        if not rect.contains(event.position()):
            return
        ranges = self._ranges()
        if ranges is None:
            return
        t_min, t_max, _v_min, _v_max = ranges
        ratio = (event.position().x() - rect.left()) / rect.width()
        target = t_min + max(0.0, min(1.0, ratio)) * (t_max - t_min)
        index = bisect_left(self._times, target)
        if index >= len(self._times):
            index = len(self._times) - 1
        elif index > 0 and abs(self._times[index - 1] - target) <= abs(self._times[index] - target):
            index -= 1
        self._cursor_index = index
        self.cursor_changed.emit(index, self._times[index], self._volts[index])
        self.update()


class DSOX3000Panel(QWidget):
    """Virtual front-panel surface for Keysight DSO-X 3000 scopes."""

    operation_requested = Signal(str, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._last_screenshot_data = b""
        self._last_screenshot_format = "PNG"
        self._last_waveform_times: tuple[float, ...] = ()
        self._last_waveform_volts: tuple[float, ...] = ()
        self._last_waveform_source = ""
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

        self.view_tabs = QTabWidget()
        root.addWidget(self.view_tabs, 1)

        screen_tab = QWidget()
        screen_layout = QVBoxLayout(screen_tab)
        preview_note = QLabel(
            "显示真实仪表屏幕截图。PNG/BMP 数据由 :DISPlay:DATA? 的 "
            "IEEE 488.2 binary block 获取。"
        )
        preview_note.setWordWrap(True)
        screen_layout.addWidget(preview_note)

        self.screen_label = QLabel("尚未读取仪表截图。")
        self.screen_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screen_label.setMinimumSize(420, 220)
        self.screen_label.setStyleSheet(
            "QLabel { border: 1px solid #777; background: #111; color: #ddd; }"
        )
        screen_layout.addWidget(self.screen_label, 1)

        preview_actions = QHBoxLayout()
        refresh_screen_button = QPushButton("刷新截图")
        refresh_screen_button.clicked.connect(self._screenshot)
        preview_actions.addWidget(refresh_screen_button)

        self.save_screenshot_button = QPushButton("保存截图")
        self.save_screenshot_button.setEnabled(False)
        self.save_screenshot_button.clicked.connect(self._save_screenshot)
        preview_actions.addWidget(self.save_screenshot_button)
        preview_actions.addStretch(1)
        screen_layout.addLayout(preview_actions)
        self.view_tabs.addTab(screen_tab, "Instrument Screen")

        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        waveform_actions = QHBoxLayout()
        acquire_waveform_button = QPushButton("Single + 读取波形")
        acquire_waveform_button.clicked.connect(self._single_waveform)
        waveform_actions.addWidget(acquire_waveform_button)
        waveform_actions.addWidget(QLabel("Timeout (s)"))
        self.waveform_timeout_edit = QLineEdit("30")
        self.waveform_timeout_edit.setMaximumWidth(80)
        waveform_actions.addWidget(self.waveform_timeout_edit)
        self.save_waveform_button = QPushButton("保存 CSV")
        self.save_waveform_button.setEnabled(False)
        self.save_waveform_button.clicked.connect(self._save_waveform_csv)
        waveform_actions.addWidget(self.save_waveform_button)
        waveform_actions.addStretch(1)
        data_layout.addLayout(waveform_actions)

        self.waveform_summary = QLabel("尚未读取 Single waveform。")
        self.waveform_summary.setWordWrap(True)
        data_layout.addWidget(self.waveform_summary)

        self.waveform_plot = WaveformPlotWidget()
        self.waveform_plot.cursor_changed.connect(self._waveform_cursor_changed)
        data_layout.addWidget(self.waveform_plot, 1)

        self.waveform_cursor_label = QLabel("Cursor: -")
        data_layout.addWidget(self.waveform_cursor_label)
        self.view_tabs.addTab(data_tab, "Data View")

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

    def _single_waveform(self) -> None:
        timeout_text = self.waveform_timeout_edit.text().strip() or "30"
        try:
            timeout_s = float(timeout_text)
        except ValueError:
            self.status_label.setText("Waveform Timeout 必须是数字。")
            return
        if timeout_s <= 0:
            self.status_label.setText("Waveform Timeout 必须大于 0。")
            return
        self._emit(
            "keysight.dsox3000.single_waveform",
            {"channel": self._channel(), "timeout_s": timeout_s},
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

    def _save_waveform_csv(self) -> None:
        if not self._last_waveform_times:
            return
        path_text, _ = QFileDialog.getSaveFileName(
            self,
            "保存波形 CSV",
            f"dsox_{self._last_waveform_source or 'waveform'}.csv",
            "CSV (*.csv);;All files (*)",
        )
        if not path_text:
            return

        with Path(path_text).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["time_s", "voltage_v"])
            writer.writerows(zip(self._last_waveform_times, self._last_waveform_volts))
        self.status_label.setText(f"波形 CSV 已保存：{path_text}")

    def _waveform_cursor_changed(self, index: int, time_s: float, voltage_v: float) -> None:
        self.waveform_cursor_label.setText(
            f"Cursor: #{index} | t={time_s:.9g} s | V={voltage_v:.9g} V"
        )

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
        elif kind == "keysight_dsox3000_single_waveform":
            self._render_waveform(result)
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
        self.view_tabs.setCurrentIndex(0)
        restore_error = result.get("inksaver_restore_error")
        message = (
            f"Screenshot: {result.get('format')} / {result.get('palette')} / "
            f"{result.get('byte_count')} bytes"
        )
        if restore_error:
            message += f" | INKSaver restore warning: {restore_error}"
        self.status_label.setText(message)

    def _render_waveform(self, result: dict[str, object]) -> None:
        times_raw = result.get("time_seconds")
        volts_raw = result.get("voltage_volts")
        if not isinstance(times_raw, (list, tuple)) or not isinstance(volts_raw, (list, tuple)):
            self.status_label.setText("Waveform operation did not return numeric arrays.")
            return

        try:
            times = tuple(float(value) for value in times_raw)
            volts = tuple(float(value) for value in volts_raw)
        except (TypeError, ValueError):
            self.status_label.setText("Waveform arrays contain non-numeric values.")
            return
        if not times or len(times) != len(volts):
            self.status_label.setText("Waveform arrays are empty or length-mismatched.")
            return

        self._last_waveform_times = times
        self._last_waveform_volts = volts
        self._last_waveform_source = str(result.get("source", "waveform"))
        self.waveform_plot.set_waveform(times, volts)
        self.save_waveform_button.setEnabled(True)
        self.waveform_cursor_label.setText("Cursor: 把鼠标移动到波形上查看采样点")
        self.waveform_summary.setText(
            "{source} | Points: {points} | Time: {start:.9g} .. {stop:.9g} s | "
            "Voltage: {vmin:.9g} .. {vmax:.9g} V".format(
                source=result.get("source", "-"),
                points=result.get("point_count", len(times)),
                start=times[0],
                stop=times[-1],
                vmin=min(volts),
                vmax=max(volts),
            )
        )
        self.view_tabs.setCurrentIndex(1)
        self.status_label.setText(
            f"Single waveform 读取完成：{len(times)} points / {result.get('source', '-')}"
        )

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
