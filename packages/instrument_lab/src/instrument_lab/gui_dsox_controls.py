"""Writable DSO-X control-panel extensions.

The base DSOX3000Panel owns screenshot, waveform and Snapshot views. This module
adds the small set of front-panel-like controls whose SCPI mappings are already
manual-verified, while continuing to emit only registered Instrument Operations.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
)

from .dsox_control_operations import ensure_dsox_control_operations_registered
from .gui_panels import DSOX3000Panel


ensure_dsox_control_operations_registered()


class DSOX3000ControlPanel(DSOX3000Panel):
    """DSO-X panel with Channel Display and common Edge Trigger write controls."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_write_controls()

    def _build_write_controls(self) -> None:
        container = QGroupBox("可写控制 / Writable Controls")
        grid = QGridLayout(container)

        channel_group = QGroupBox("Channel Display")
        channel_layout = QFormLayout(channel_group)
        self.channel_display_combo = QComboBox()
        self.channel_display_combo.addItems(["ON", "OFF"])
        channel_button = QPushButton("应用 Display")
        channel_button.clicked.connect(self._apply_channel_display)
        channel_layout.addRow("当前 Channel", QLabel("使用顶部 Channel 选择"))
        channel_layout.addRow("Display", self.channel_display_combo)
        channel_layout.addRow(channel_button)
        grid.addWidget(channel_group, 0, 0)

        trigger_group = QGroupBox("Edge Trigger")
        trigger_layout = QFormLayout(trigger_group)
        self.edge_mode_note = QLabel("当前 Mode：-")
        self.edge_mode_note.setWordWrap(True)
        self.trigger_sweep_combo = QComboBox()
        self.trigger_sweep_combo.addItems(["AUTO", "NORM"])
        self.trigger_source_combo = QComboBox()
        self.trigger_source_combo.addItems(["CH1", "CH2", "CH3", "CH4"])
        self.trigger_level_edit = QLineEdit()
        self.trigger_level_edit.setPlaceholderText("V；留空保持当前值")
        trigger_button = QPushButton("应用 Edge Trigger")
        trigger_button.clicked.connect(self._apply_edge_trigger)
        trigger_layout.addRow(self.edge_mode_note)
        trigger_layout.addRow("Sweep", self.trigger_sweep_combo)
        trigger_layout.addRow("Source", self.trigger_source_combo)
        trigger_layout.addRow("Level (V)", self.trigger_level_edit)
        trigger_layout.addRow(trigger_button)
        grid.addWidget(trigger_group, 0, 1)

        note = QLabel(
            "Edge Trigger 快捷设置不会自动修改 Trigger Mode；如果当前 Mode 不是 EDGE，"
            "先在仪表前面板或工程调试区切换到 EDGE，再使用这里的 Sweep/Source/Level。"
        )
        note.setWordWrap(True)
        grid.addWidget(note, 1, 0, 1, 2)

        layout = self.layout()
        if layout is not None:
            layout.insertWidget(4, container)

    def _apply_channel_display(self) -> None:
        self._emit(
            "keysight.dsox3000.set_channel_display",
            {
                "channel": self._channel(),
                "state": self.channel_display_combo.currentText(),
            },
        )

    def _apply_edge_trigger(self) -> None:
        level_text = self.trigger_level_edit.text().strip()
        if level_text:
            try:
                float(level_text)
            except ValueError:
                self.status_label.setText("Trigger Level 必须是数字，或留空保持当前值。")
                return

        self._emit(
            "keysight.dsox3000.set_edge_trigger",
            {
                "sweep": self.trigger_sweep_combo.currentText(),
                "source": self.trigger_source_combo.currentText(),
                "level_v": level_text,
            },
        )

    @staticmethod
    def _normalize_source_for_combo(value: object) -> str | None:
        text = str(value).strip().upper().replace("NEL", "")
        aliases = {
            "CHAN1": "CH1",
            "CH1": "CH1",
            "CHAN2": "CH2",
            "CH2": "CH2",
            "CHAN3": "CH3",
            "CH3": "CH3",
            "CHAN4": "CH4",
            "CH4": "CH4",
        }
        return aliases.get(text)

    def _render_control_state(self, result: dict[str, object]) -> None:
        super()._render_control_state(result)

        display_text = "ON" if bool(result.get("channel_display")) else "OFF"
        index = self.channel_display_combo.findText(display_text)
        if index >= 0:
            self.channel_display_combo.setCurrentIndex(index)

        sweep = str(result.get("trigger_sweep", "")).strip().upper()
        sweep_index = self.trigger_sweep_combo.findText(sweep)
        if sweep_index >= 0:
            self.trigger_sweep_combo.setCurrentIndex(sweep_index)

        source = self._normalize_source_for_combo(result.get("trigger_source", ""))
        if source is not None:
            source_index = self.trigger_source_combo.findText(source)
            if source_index >= 0:
                self.trigger_source_combo.setCurrentIndex(source_index)

        level = result.get("trigger_level_v")
        if level is not None:
            self.trigger_level_edit.setText(self._number(level))

        mode = str(result.get("trigger_mode", "-")).strip()
        self.edge_mode_note.setText(f"当前 Mode：{mode}")
