"""Composed writable DSO-X controls.

The stable :class:`DSOX3000Panel` owns the hardware-verified Screenshot,
Data View and Snapshot render paths. Writable Channel/Trigger controls are kept
in a separate sibling widget and are composed beside the stable panel instead of
subclassing or mutating it.

This separation is intentional. A previous subclass-based extension correlated
with a native Windows/PySide6 exit when refreshing screenshots. Composition
keeps the exact verified panel object in the screenshot path while still exposing
the reusable Driver/Operation control APIs.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .dsox_control_operations import ensure_dsox_control_operations_registered
from .gui_panels import DSOX3000Panel


ensure_dsox_control_operations_registered()


def _tune_main_panel_layout(panel: DSOX3000Panel) -> None:
    """Rebalance the verified DSO-X panel for the new full-width workspace.

    The screenshot renderer itself is intentionally untouched.  We only keep its
    QLabel from stretching across the entire custom-control page, center it, and
    reserve more vertical room by capping the always-visible Snapshot table.
    """

    panel.screen_label.setMinimumSize(700, 400)
    panel.screen_label.setMaximumSize(760, 440)

    screen_parent = panel.screen_label.parentWidget()
    screen_layout = screen_parent.layout() if screen_parent is not None else None
    if screen_layout is not None:
        screen_layout.setAlignment(
            panel.screen_label,
            Qt.AlignmentFlag.AlignHCenter,
        )

    # Snapshot remains available below the main view, but it should not consume
    # half of the new large page while the user is looking at Instrument Screen.
    panel.snapshot_table.setMaximumHeight(180)


class DSOX3000WritableControls(QWidget):
    """Small standalone widget for Channel Display and Edge Trigger writes."""

    operation_requested = Signal(str, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        note = QLabel(
            "这里的写控制与 Screenshot / Data View 主面板完全分离。"
            "所有设置仍通过 Driver / Instrument Operation 执行。"
        )
        note.setWordWrap(True)
        root.addWidget(note)

        self.status_label = QLabel("可先读取当前状态，再修改需要的参数。")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        channel_group = QGroupBox("Channel Display")
        channel_layout = QFormLayout(channel_group)
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["1", "2", "3", "4"])
        self.channel_display_combo = QComboBox()
        self.channel_display_combo.addItems(["ON", "OFF"])

        channel_refresh = QPushButton("读取 Channel / Trigger 状态")
        channel_refresh.clicked.connect(self._read_state)
        channel_apply = QPushButton("应用 Display")
        channel_apply.clicked.connect(self._apply_channel_display)

        channel_layout.addRow("Channel", self.channel_combo)
        channel_layout.addRow("Display", self.channel_display_combo)
        channel_layout.addRow(channel_refresh)
        channel_layout.addRow(channel_apply)
        root.addWidget(channel_group)

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

        trigger_apply = QPushButton("应用 Edge Trigger")
        trigger_apply.clicked.connect(self._apply_edge_trigger)

        trigger_layout.addRow(self.edge_mode_note)
        trigger_layout.addRow("Sweep", self.trigger_sweep_combo)
        trigger_layout.addRow("Source", self.trigger_source_combo)
        trigger_layout.addRow("Level (V)", self.trigger_level_edit)
        trigger_layout.addRow(trigger_apply)
        root.addWidget(trigger_group)

        safety_note = QLabel(
            "Edge Trigger 快捷设置不会自动修改 Trigger Mode。"
            "如果当前 Mode 不是 EDGE，请先明确切换到 EDGE。"
        )
        safety_note.setWordWrap(True)
        root.addWidget(safety_note)
        root.addStretch(1)

    def _emit(self, operation_id: str, parameters: dict[str, object]) -> None:
        self.status_label.setText(f"准备执行：{operation_id}")
        self.operation_requested.emit(operation_id, parameters)

    def _read_state(self) -> None:
        self._emit(
            "keysight.dsox3000.read_control_state",
            {"channel": self.channel_combo.currentText()},
        )

    def _apply_channel_display(self) -> None:
        self._emit(
            "keysight.dsox3000.set_channel_display",
            {
                "channel": self.channel_combo.currentText(),
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
    def _normalize_source(value: object) -> str | None:
        text = str(value).strip().upper()
        aliases = {
            "CHANNEL1": "CH1",
            "CHANNEL2": "CH2",
            "CHANNEL3": "CH3",
            "CHANNEL4": "CH4",
            "CHAN1": "CH1",
            "CHAN2": "CH2",
            "CHAN3": "CH3",
            "CHAN4": "CH4",
            "CH1": "CH1",
            "CH2": "CH2",
            "CH3": "CH3",
            "CH4": "CH4",
        }
        return aliases.get(text)

    @staticmethod
    def _number(value: object) -> str:
        try:
            return f"{float(value):.12g}"
        except (TypeError, ValueError):
            return str(value)

    def _render_control_state(self, result: dict[str, object]) -> None:
        channel = str(result.get("channel", ""))
        channel_index = self.channel_combo.findText(channel)
        if channel_index >= 0:
            self.channel_combo.setCurrentIndex(channel_index)

        display = "ON" if bool(result.get("channel_display")) else "OFF"
        display_index = self.channel_display_combo.findText(display)
        if display_index >= 0:
            self.channel_display_combo.setCurrentIndex(display_index)

        sweep = str(result.get("trigger_sweep", "")).strip().upper()
        sweep_index = self.trigger_sweep_combo.findText(sweep)
        if sweep_index >= 0:
            self.trigger_sweep_combo.setCurrentIndex(sweep_index)

        source = self._normalize_source(result.get("trigger_source", ""))
        if source is not None:
            source_index = self.trigger_source_combo.findText(source)
            if source_index >= 0:
                self.trigger_source_combo.setCurrentIndex(source_index)

        level = result.get("trigger_level_v")
        if level is not None:
            self.trigger_level_edit.setText(self._number(level))

        mode = str(result.get("trigger_mode", "-")).strip()
        self.edge_mode_note.setText(f"当前 Mode：{mode}")
        self.status_label.setText("当前 Channel / Trigger 状态已同步。")

    def handle_operation_result(
        self,
        operation_id: str,
        result: object,
        elapsed_ms: float,
    ) -> None:
        if not isinstance(result, dict):
            return

        if operation_id == "keysight.dsox3000.read_control_state":
            self._render_control_state(result)
            return

        if operation_id == "keysight.dsox3000.set_channel_display":
            applied = result.get("applied", {})
            if isinstance(applied, dict):
                state = applied.get("state", "-")
                channel = applied.get("channel", "-")
                self.status_label.setText(
                    f"CH{channel} Display 已发送：{state} ({elapsed_ms:.0f} ms)"
                )
            return

        if operation_id == "keysight.dsox3000.set_edge_trigger":
            self.status_label.setText(
                f"Edge Trigger 设置已发送 ({elapsed_ms:.0f} ms)，建议重新读取状态确认。"
            )


class DSOX3000ControlPanel(QWidget):
    """Composite DSO-X workspace preserving the exact stable main panel."""

    operation_requested = Signal(str, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget(self)
        root.addWidget(self.tabs)

        # Do not subclass or patch the verified renderer. Only apply benign
        # geometry tuning after construction for the new full-width workspace.
        self.main_panel = DSOX3000Panel(self.tabs)
        _tune_main_panel_layout(self.main_panel)
        self.main_panel.operation_requested.connect(self.operation_requested.emit)
        self.tabs.addTab(self.main_panel, "主控制台")

        self.writable_controls = DSOX3000WritableControls(self.tabs)
        self.writable_controls.operation_requested.connect(
            self.operation_requested.emit
        )
        self.tabs.addTab(self.writable_controls, "快速设置")

    def handle_operation_result(
        self,
        operation_id: str,
        result: object,
        elapsed_ms: float,
    ) -> None:
        # The stable main panel remains the sole owner of screenshot/waveform/
        # Snapshot rendering. The lightweight controls sibling only reacts to
        # control-state and write-operation results.
        self.main_panel.handle_operation_result(
            operation_id,
            result,
            elapsed_ms,
        )
        self.writable_controls.handle_operation_result(
            operation_id,
            result,
            elapsed_ms,
        )
