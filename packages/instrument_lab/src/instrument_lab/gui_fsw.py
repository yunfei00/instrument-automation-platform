"""Qt control surface for Rohde & Schwarz FSW analyzers.

The panel is intentionally thin: it renders state and emits registered FSW
Instrument Operations. VISA ownership and SCPI strings stay below the GUI.
"""

from __future__ import annotations

from bisect import bisect_left
import csv
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .fsw_operations import ensure_fsw_operations_registered


ensure_fsw_operations_registered()


class SpectrumPlotWidget(QWidget):
    """Small dependency-free spectrum renderer with cursor support."""

    cursor_changed = Signal(int, float, float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._frequencies: tuple[float, ...] = ()
        self._levels: tuple[float, ...] = ()
        self._cursor_index: int | None = None
        self.setMinimumSize(640, 360)
        self.setMouseTracking(True)

    def set_trace(
        self,
        frequencies_hz: tuple[float, ...],
        levels_dbm: tuple[float, ...],
    ) -> None:
        if len(frequencies_hz) != len(levels_dbm):
            raise ValueError("Spectrum frequency/level arrays must have equal length")
        self._frequencies = frequencies_hz
        self._levels = levels_dbm
        self._cursor_index = None
        self.update()

    def clear_trace(self) -> None:
        self._frequencies = ()
        self._levels = ()
        self._cursor_index = None
        self.update()

    def _plot_rect(self) -> QRectF:
        return QRectF(
            70.0,
            18.0,
            max(10.0, self.width() - 92.0),
            max(10.0, self.height() - 62.0),
        )

    @staticmethod
    def _expanded_range(low: float, high: float) -> tuple[float, float]:
        if high > low:
            padding = (high - low) * 0.05
            return low - padding, high + padding
        padding = max(abs(low) * 0.05, 1.0)
        return low - padding, high + padding

    def _ranges(self) -> tuple[float, float, float, float] | None:
        if not self._frequencies or not self._levels:
            return None
        f_min, f_max = self._expanded_range(
            self._frequencies[0],
            self._frequencies[-1],
        )
        y_min, y_max = self._expanded_range(min(self._levels), max(self._levels))
        return f_min, f_max, y_min, y_max

    @staticmethod
    def _map_point(
        frequency_hz: float,
        level_dbm: float,
        rect: QRectF,
        ranges: tuple[float, float, float, float],
    ) -> QPointF:
        f_min, f_max, y_min, y_max = ranges
        x = rect.left() + (frequency_hz - f_min) / (f_max - f_min) * rect.width()
        y = rect.bottom() - (level_dbm - y_min) / (y_max - y_min) * rect.height()
        return QPointF(x, y)

    @staticmethod
    def _format_frequency(value_hz: float) -> str:
        magnitude = abs(value_hz)
        if magnitude >= 1e9:
            return f"{value_hz / 1e9:.6g} GHz"
        if magnitude >= 1e6:
            return f"{value_hz / 1e6:.6g} MHz"
        if magnitude >= 1e3:
            return f"{value_hz / 1e3:.6g} kHz"
        return f"{value_hz:.6g} Hz"

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt API
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
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "尚未读取 Spectrum Trace")
            return

        f_min, f_max, y_min, y_max = ranges
        painter.setPen(QColor(190, 195, 200))
        painter.drawText(4, 28, f"{y_max:.6g} dBm")
        painter.drawText(4, int(rect.bottom()), f"{y_min:.6g} dBm")
        painter.drawText(
            int(rect.left()),
            self.height() - 12,
            self._format_frequency(f_min),
        )
        painter.drawText(
            int(rect.right() - 145),
            self.height() - 12,
            self._format_frequency(f_max),
        )

        max_visual_points = max(1200, int(rect.width() * 2.0))
        count = len(self._frequencies)
        stride = max(1, count // max_visual_points)
        polygon = QPolygonF()
        for index in range(0, count, stride):
            polygon.append(
                self._map_point(
                    self._frequencies[index],
                    self._levels[index],
                    rect,
                    ranges,
                )
            )
        if count > 1 and (count - 1) % stride:
            polygon.append(
                self._map_point(
                    self._frequencies[-1],
                    self._levels[-1],
                    rect,
                    ranges,
                )
            )
        painter.setPen(QPen(QColor(92, 220, 110), 1.4))
        painter.drawPolyline(polygon)

        if self._cursor_index is not None and 0 <= self._cursor_index < count:
            point = self._map_point(
                self._frequencies[self._cursor_index],
                self._levels[self._cursor_index],
                rect,
                ranges,
            )
            painter.setPen(QPen(QColor(90, 190, 255), 1))
            painter.drawLine(QPointF(point.x(), rect.top()), QPointF(point.x(), rect.bottom()))
            painter.drawLine(QPointF(rect.left(), point.y()), QPointF(rect.right(), point.y()))
            painter.setBrush(QColor(90, 190, 255))
            painter.drawEllipse(point, 3.0, 3.0)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt API
        if not self._frequencies:
            return
        rect = self._plot_rect()
        if not rect.contains(event.position()):
            return
        ranges = self._ranges()
        if ranges is None:
            return
        f_min, f_max, _y_min, _y_max = ranges
        ratio = (event.position().x() - rect.left()) / rect.width()
        target = f_min + max(0.0, min(1.0, ratio)) * (f_max - f_min)
        index = bisect_left(self._frequencies, target)
        if index >= len(self._frequencies):
            index = len(self._frequencies) - 1
        elif index > 0 and abs(self._frequencies[index - 1] - target) <= abs(
            self._frequencies[index] - target
        ):
            index -= 1
        self._cursor_index = index
        self.cursor_changed.emit(
            index,
            self._frequencies[index],
            self._levels[index],
        )
        self.update()


class FSWControlPanel(QWidget):
    """Dedicated FSW control surface with controls left and spectrum right."""

    operation_requested = Signal(str, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._last_frequencies: tuple[float, ...] = ()
        self._last_levels: tuple[float, ...] = ()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)

        title = QLabel("Rohde & Schwarz FSW 专用控制台")
        title.setStyleSheet("font-weight: 600; font-size: 17px;")
        root.addWidget(title)

        self.status_label = QLabel(
            "Phase 1：Frequency / Bandwidth / RF Input / Continuous / Spectrum Trace。"
        )
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        self.workspace_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.workspace_splitter.setChildrenCollapsible(False)
        root.addWidget(self.workspace_splitter, 1)

        # Left: compact controls. Keep its width bounded so the spectrum remains
        # the visual focus, and make the column scrollable on smaller displays.
        control_scroll = QScrollArea(self.workspace_splitter)
        control_scroll.setWidgetResizable(True)
        control_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        control_scroll.setMinimumWidth(360)
        control_scroll.setMaximumWidth(500)

        control_page = QWidget(control_scroll)
        control_layout = QVBoxLayout(control_page)
        control_layout.setContentsMargins(6, 6, 6, 6)

        action_group = QGroupBox("Acquisition")
        action_layout = QFormLayout(action_group)
        read_button = QPushButton("读取当前状态")
        read_button.clicked.connect(
            lambda: self._emit("rohde_schwarz.fsw.read_control_state", {})
        )
        self.continuous_combo = QComboBox()
        self.continuous_combo.addItems(["ON", "OFF"])
        continuous_button = QPushButton("应用 Continuous")
        continuous_button.clicked.connect(self._apply_continuous)
        action_layout.addRow(read_button)
        action_layout.addRow("Continuous", self.continuous_combo)
        action_layout.addRow(continuous_button)
        control_layout.addWidget(action_group)

        center_group = QGroupBox("Frequency · Center / Span")
        center_layout = QFormLayout(center_group)
        self.center_edit = QLineEdit()
        self.center_edit.setPlaceholderText("Hz，例如 750e6")
        self.span_edit = QLineEdit()
        self.span_edit.setPlaceholderText("Hz，例如 100e6")
        center_apply = QPushButton("应用 Center / Span")
        center_apply.clicked.connect(self._apply_center_span)
        center_layout.addRow("Center (Hz)", self.center_edit)
        center_layout.addRow("Span (Hz)", self.span_edit)
        center_layout.addRow(center_apply)
        control_layout.addWidget(center_group)

        start_group = QGroupBox("Frequency · Start / Stop")
        start_layout = QFormLayout(start_group)
        self.start_edit = QLineEdit()
        self.start_edit.setPlaceholderText("Hz")
        self.stop_edit = QLineEdit()
        self.stop_edit.setPlaceholderText("Hz")
        start_apply = QPushButton("应用 Start / Stop")
        start_apply.clicked.connect(self._apply_start_stop)
        start_layout.addRow("Start (Hz)", self.start_edit)
        start_layout.addRow("Stop (Hz)", self.stop_edit)
        start_layout.addRow(start_apply)
        control_layout.addWidget(start_group)

        bandwidth_group = QGroupBox("Bandwidth")
        bandwidth_layout = QFormLayout(bandwidth_group)
        self.rbw_edit = QLineEdit()
        self.rbw_edit.setPlaceholderText("Hz")
        self.vbw_edit = QLineEdit()
        self.vbw_edit.setPlaceholderText("Hz")
        bandwidth_apply = QPushButton("应用 RBW / VBW")
        bandwidth_apply.clicked.connect(self._apply_bandwidth)
        bandwidth_layout.addRow("RBW (Hz)", self.rbw_edit)
        bandwidth_layout.addRow("VBW (Hz)", self.vbw_edit)
        bandwidth_layout.addRow(bandwidth_apply)
        control_layout.addWidget(bandwidth_group)

        input_group = QGroupBox("RF Input")
        input_layout = QFormLayout(input_group)
        self.atten_mode_combo = QComboBox()
        self.atten_mode_combo.addItems(["AUTO", "MANUAL"])
        self.atten_edit = QLineEdit()
        self.atten_edit.setPlaceholderText("dB；AUTO 时可留空")
        self.preamp_combo = QComboBox()
        self.preamp_combo.addItems(["0", "15", "30"])
        input_apply = QPushButton("应用 RF Input")
        input_apply.clicked.connect(self._apply_input)
        input_layout.addRow("RF Atten", self.atten_mode_combo)
        input_layout.addRow("Manual Atten (dB)", self.atten_edit)
        input_layout.addRow("Preamp (dB)", self.preamp_combo)
        input_layout.addRow(input_apply)
        control_layout.addWidget(input_group)

        state_group = QGroupBox("当前状态")
        state_layout = QFormLayout(state_group)
        self.sweep_time_label = QLabel("-")
        self.trigger_source_label = QLabel("-")
        self.reference_level_label = QLabel("待实机资格验证，本阶段不自动读取")
        self.reference_level_label.setWordWrap(True)
        state_layout.addRow("Sweep Time", self.sweep_time_label)
        state_layout.addRow("Trigger Source", self.trigger_source_label)
        state_layout.addRow("Reference Level", self.reference_level_label)
        control_layout.addWidget(state_group)
        control_layout.addStretch(1)
        control_scroll.setWidget(control_page)
        self.workspace_splitter.addWidget(control_scroll)
        self.control_scroll = control_scroll

        # Right: large instrument data area. Keep a tab host even though phase 1
        # only contains Spectrum Data View so a future real-screen view can be
        # added without disturbing the left control column.
        self.view_tabs = QTabWidget(self.workspace_splitter)
        self.workspace_splitter.addWidget(self.view_tabs)
        self.workspace_splitter.setStretchFactor(0, 0)
        self.workspace_splitter.setStretchFactor(1, 1)
        self.workspace_splitter.setSizes([420, 980])

        data_tab = QWidget(self.view_tabs)
        data_layout = QVBoxLayout(data_tab)
        trace_actions = QHBoxLayout()
        trace_button = QPushButton("Single + 读取 Spectrum Trace")
        trace_button.clicked.connect(self._single_trace)
        trace_actions.addWidget(trace_button)
        trace_actions.addWidget(QLabel("Timeout (s)"))
        self.trace_timeout_edit = QLineEdit("30")
        self.trace_timeout_edit.setMaximumWidth(90)
        trace_actions.addWidget(self.trace_timeout_edit)
        self.save_csv_button = QPushButton("保存 CSV")
        self.save_csv_button.setEnabled(False)
        self.save_csv_button.clicked.connect(self._save_csv)
        trace_actions.addWidget(self.save_csv_button)
        trace_actions.addStretch(1)
        data_layout.addLayout(trace_actions)

        self.trace_summary = QLabel("尚未读取 Spectrum Trace。")
        self.trace_summary.setWordWrap(True)
        data_layout.addWidget(self.trace_summary)

        self.spectrum_plot = SpectrumPlotWidget()
        self.spectrum_plot.cursor_changed.connect(self._cursor_changed)
        data_layout.addWidget(self.spectrum_plot, 1)

        self.cursor_label = QLabel("Cursor: -")
        data_layout.addWidget(self.cursor_label)
        self.view_tabs.addTab(data_tab, "Spectrum Data View")

    def _emit(self, operation_id: str, parameters: dict[str, object]) -> None:
        self.status_label.setText(f"准备执行：{operation_id}")
        self.operation_requested.emit(operation_id, parameters)

    @staticmethod
    def _float_text(edit: QLineEdit, label: str) -> str:
        text = edit.text().strip()
        if text:
            try:
                float(text)
            except ValueError as exc:
                raise ValueError(f"{label} 必须是数字") from exc
        return text

    def _apply_center_span(self) -> None:
        try:
            center = self._float_text(self.center_edit, "Center")
            span = self._float_text(self.span_edit, "Span")
        except ValueError as exc:
            self.status_label.setText(str(exc))
            return
        self._emit(
            "rohde_schwarz.fsw.set_center_span",
            {"center_hz": center, "span_hz": span},
        )

    def _apply_start_stop(self) -> None:
        try:
            start = self._float_text(self.start_edit, "Start")
            stop = self._float_text(self.stop_edit, "Stop")
        except ValueError as exc:
            self.status_label.setText(str(exc))
            return
        self._emit(
            "rohde_schwarz.fsw.set_start_stop",
            {"start_hz": start, "stop_hz": stop},
        )

    def _apply_bandwidth(self) -> None:
        try:
            rbw = self._float_text(self.rbw_edit, "RBW")
            vbw = self._float_text(self.vbw_edit, "VBW")
        except ValueError as exc:
            self.status_label.setText(str(exc))
            return
        self._emit(
            "rohde_schwarz.fsw.set_bandwidth",
            {"rbw_hz": rbw, "vbw_hz": vbw},
        )

    def _apply_input(self) -> None:
        try:
            attenuation = self._float_text(self.atten_edit, "RF Attenuation")
        except ValueError as exc:
            self.status_label.setText(str(exc))
            return
        self._emit(
            "rohde_schwarz.fsw.set_input",
            {
                "attenuation_mode": self.atten_mode_combo.currentText(),
                "attenuation_db": attenuation,
                "preamp_db": self.preamp_combo.currentText(),
            },
        )

    def _apply_continuous(self) -> None:
        self._emit(
            "rohde_schwarz.fsw.set_continuous",
            {"state": self.continuous_combo.currentText()},
        )

    def _single_trace(self) -> None:
        try:
            timeout = float(self.trace_timeout_edit.text().strip())
        except ValueError:
            self.status_label.setText("Trace Timeout 必须是数字。")
            return
        if timeout <= 0:
            self.status_label.setText("Trace Timeout 必须大于 0。")
            return
        self.view_tabs.setCurrentIndex(0)
        self._emit(
            "rohde_schwarz.fsw.single_trace",
            {"timeout_s": timeout},
        )

    @staticmethod
    def _number(value: object) -> str:
        try:
            return f"{float(value):.12g}"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _frequency(value: object) -> str:
        try:
            hz = float(value)
        except (TypeError, ValueError):
            return str(value)
        if abs(hz) >= 1e9:
            return f"{hz / 1e9:.9g} GHz"
        if abs(hz) >= 1e6:
            return f"{hz / 1e6:.9g} MHz"
        if abs(hz) >= 1e3:
            return f"{hz / 1e3:.9g} kHz"
        return f"{hz:.9g} Hz"

    def _render_state(self, result: dict[str, object]) -> None:
        mapping = (
            (self.center_edit, "center_hz"),
            (self.span_edit, "span_hz"),
            (self.start_edit, "start_hz"),
            (self.stop_edit, "stop_hz"),
            (self.rbw_edit, "rbw_hz"),
            (self.vbw_edit, "vbw_hz"),
        )
        for edit, key in mapping:
            value = result.get(key)
            if value is not None:
                edit.setText(self._number(value))

        continuous = "ON" if bool(result.get("continuous")) else "OFF"
        index = self.continuous_combo.findText(continuous)
        if index >= 0:
            self.continuous_combo.setCurrentIndex(index)

        atten_auto = bool(result.get("rf_attenuation_auto"))
        atten_mode = "AUTO" if atten_auto else "MANUAL"
        index = self.atten_mode_combo.findText(atten_mode)
        if index >= 0:
            self.atten_mode_combo.setCurrentIndex(index)
        attenuation = result.get("rf_attenuation_db")
        if attenuation is not None:
            self.atten_edit.setText(self._number(attenuation))

        preamp = str(int(float(result.get("preamp_db", 0))))
        index = self.preamp_combo.findText(preamp)
        if index >= 0:
            self.preamp_combo.setCurrentIndex(index)

        sweep_time = result.get("sweep_time_s")
        self.sweep_time_label.setText(
            "-" if sweep_time is None else f"{self._number(sweep_time)} s"
        )
        self.trigger_source_label.setText(str(result.get("trigger_source", "-")))
        self.status_label.setText(
            "FSW 状态已同步：Frequency / Bandwidth / RF Input / Continuous。"
        )

    def _render_trace(self, result: dict[str, object]) -> None:
        frequencies = result.get("frequencies_hz")
        levels = result.get("levels_dbm")
        if not isinstance(frequencies, (tuple, list)) or not isinstance(
            levels, (tuple, list)
        ):
            self.status_label.setText("Spectrum Trace 返回结构不完整。")
            return

        self._last_frequencies = tuple(float(value) for value in frequencies)
        self._last_levels = tuple(float(value) for value in levels)
        self.spectrum_plot.set_trace(self._last_frequencies, self._last_levels)
        self.save_csv_button.setEnabled(bool(self._last_frequencies))

        points = int(result.get("points", len(self._last_levels)))
        peak_f = result.get("peak_frequency_hz")
        peak_level = result.get("peak_level_dbm")
        peak_text = "-"
        if peak_f is not None and peak_level is not None:
            peak_text = f"{self._frequency(peak_f)} / {self._number(peak_level)} dBm"
        self.trace_summary.setText(
            f"Points: {points} | "
            f"Range: {self._frequency(result.get('start_hz'))} .. "
            f"{self._frequency(result.get('stop_hz'))} | Peak: {peak_text}"
        )
        self.status_label.setText("Single Spectrum Trace 读取完成。")
        self.view_tabs.setCurrentIndex(0)

    def _cursor_changed(self, index: int, frequency_hz: float, level_dbm: float) -> None:
        self.cursor_label.setText(
            f"Cursor: #{index} | {self._frequency(frequency_hz)} | {level_dbm:.9g} dBm"
        )

    def _save_csv(self) -> None:
        if not self._last_frequencies:
            return
        filename, _selected = QFileDialog.getSaveFileName(
            self,
            "保存 FSW Spectrum Trace",
            "fsw_spectrum_trace.csv",
            "CSV Files (*.csv)",
        )
        if not filename:
            return
        path = Path(filename)
        if path.suffix.lower() != ".csv":
            path = path.with_suffix(".csv")
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["frequency_hz", "level_dbm"])
            writer.writerows(zip(self._last_frequencies, self._last_levels))
        self.status_label.setText(f"Spectrum CSV 已保存：{path.name}")

    def handle_operation_result(
        self,
        operation_id: str,
        result: object,
        elapsed_ms: float,
    ) -> None:
        if not isinstance(result, dict):
            return
        if operation_id == "rohde_schwarz.fsw.read_control_state":
            self._render_state(result)
            return
        if operation_id == "rohde_schwarz.fsw.single_trace":
            self._render_trace(result)
            return
        if result.get("kind") == "rohde_schwarz_fsw_setting_applied":
            setting = result.get("setting", "setting")
            self.status_label.setText(
                f"FSW {setting} 设置已发送 ({elapsed_ms:.0f} ms)，建议读取状态确认。"
            )
