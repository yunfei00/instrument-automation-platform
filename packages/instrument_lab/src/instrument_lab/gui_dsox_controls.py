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
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .dsox_control_operations import ensure_dsox_control_operations_registered
from .gui_panels import DSOX3000Panel


ensure_dsox_control_operations_registered()


class AspectPixmapLabel(QLabel):
    """Resize a screenshot to the available area while preserving its ratio."""

    def __init__(
        self,
        text: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self._source_pixmap = QPixmap()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    def setPixmap(self, pixmap: QPixmap) -> None:  # noqa: N802 - Qt API
        self._source_pixmap = QPixmap(pixmap)
        self._refresh_scaled_pixmap()

    def _refresh_scaled_pixmap(self) -> None:
        if self._source_pixmap.isNull():
            return

        target_size = self.contentsRect().size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            return

        scaled = self._source_pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        QLabel.setPixmap(self, scaled)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        self._refresh_scaled_pixmap()


def _replace_screen_label(panel: DSOX3000Panel) -> None:
    """Swap only the visual QLabel; screenshot acquisition/render ownership stays put."""

    old_label = panel.screen_label
    parent = old_label.parentWidget()
    layout = parent.layout() if parent is not None else None
    if parent is None or layout is None:
        return

    screen_label = AspectPixmapLabel(old_label.text(), parent)
    screen_label.setStyleSheet(old_label.styleSheet())
    screen_label.setToolTip(old_label.toolTip())
    screen_label.setMinimumSize(640, 400)

    layout.replaceWidget(old_label, screen_label)
    old_label.hide()
    old_label.setParent(None)
    old_label.deleteLater()
    panel.screen_label = screen_label


def _reflow_main_panel_layout(panel: DSOX3000Panel) -> None:
    """Place controls on the left and the large Screen/Data View on the right.

    ``DSOX3000Panel`` still owns every command callback and every screenshot /
    waveform result renderer.  This function only rearranges the widgets that
    the verified panel already created, so no SCPI or binary-transfer path is
    duplicated here.
    """

    root = panel.layout()
    if root is None or root.count() < 6:
        return

    # Original order is title, status, action row, settings grid, view tabs,
    # Snapshot. Take the lower four items from bottom to top so title/status stay
    # untouched at the top of the panel.
    snapshot_item = root.takeAt(5)
    view_item = root.takeAt(4)
    settings_item = root.takeAt(3)
    actions_item = root.takeAt(2)

    snapshot_group = snapshot_item.widget() if snapshot_item is not None else None
    view_tabs = view_item.widget() if view_item is not None else None
    settings_layout = settings_item.layout() if settings_item is not None else None
    actions_layout = actions_item.layout() if actions_item is not None else None

    if view_tabs is None or settings_layout is None or actions_layout is None:
        return

    _replace_screen_label(panel)

    splitter = QSplitter(Qt.Orientation.Horizontal, panel)
    splitter.setChildrenCollapsible(False)

    # Left: compact controls / state / Snapshot. A scroll area keeps the panel
    # usable on smaller displays without stealing width from the instrument view.
    left_scroll = QScrollArea(splitter)
    left_scroll.setWidgetResizable(True)
    left_scroll.setHorizontalScrollBarPolicy(
        Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    )
    left_scroll.setMinimumWidth(360)
    left_scroll.setMaximumWidth(500)

    left_content = QWidget(left_scroll)
    left_layout = QVBoxLayout(left_content)
    left_layout.setContentsMargins(6, 6, 6, 6)
    left_layout.setSpacing(8)

    actions_group = QGroupBox("常用操作", left_content)
    actions_grid = QGridLayout(actions_group)
    action_widgets: list[QWidget] = []
    while actions_layout.count():
        item = actions_layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            action_widgets.append(widget)

    channel_label = next(
        (widget for widget in action_widgets if isinstance(widget, QLabel)),
        QLabel("Channel", actions_group),
    )
    actions_grid.addWidget(channel_label, 0, 0)
    actions_grid.addWidget(panel.channel_combo, 0, 1)

    buttons = [
        widget
        for widget in action_widgets
        if isinstance(widget, QPushButton)
    ]
    for index, button in enumerate(buttons):
        row = 1 + index // 2
        column = index % 2
        actions_grid.addWidget(button, row, column)

    left_layout.addWidget(actions_group)

    # The old settings grid was 2x2. On the narrower left column, stack its four
    # groups vertically so labels and edit boxes remain readable.
    while settings_layout.count():
        item = settings_layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            left_layout.addWidget(widget)

    if snapshot_group is not None:
        panel.snapshot_table.setMaximumHeight(240)
        left_layout.addWidget(snapshot_group)

    left_layout.addStretch(1)
    left_scroll.setWidget(left_content)

    # Right: give the real screen and local Data View most of the workspace.
    view_tabs.setMinimumSize(680, 500)
    splitter.addWidget(left_scroll)
    splitter.addWidget(view_tabs)
    splitter.setStretchFactor(0, 0)
    splitter.setStretchFactor(1, 1)
    splitter.setSizes([430, 900])

    root.addWidget(splitter, 1)


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

        # Keep the verified panel object and all of its operation handlers. Only
        # rearrange the widgets after construction: controls left, Screen/Data
        # View right. No screenshot acquisition or binary parsing is changed.
        self.main_panel = DSOX3000Panel(self.tabs)
        _reflow_main_panel_layout(self.main_panel)
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
