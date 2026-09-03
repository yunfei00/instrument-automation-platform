"""Qt-only FSW Reference Level and trigger controls.

The widget emits Instrument Operation IDs only.  Candidate/manual-verified SCPI
stays below the GUI in the driver/operation layers.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .fsw_reference_trigger_operations import (
    ensure_fsw_reference_trigger_operations_registered,
)
from .gui_units import UnitValueEdit


ensure_fsw_reference_trigger_operations_registered()


class FSWReferenceTriggerControls(QWidget):
    """Explicit amplitude/trigger controls kept separate from core state refresh."""

    operation_requested = Signal(str, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        amplitude_group = QGroupBox("Amplitude · Reference Level")
        amplitude_layout = QFormLayout(amplitude_group)
        self.reference_level_edit = QLineEdit()
        self.reference_level_edit.setPlaceholderText("dBm，例如 -20")
        reference_actions = QHBoxLayout()
        read_reference = QPushButton("读取")
        read_reference.clicked.connect(self._read_reference_level)
        apply_reference = QPushButton("应用")
        apply_reference.clicked.connect(self._apply_reference_level)
        reference_actions.addWidget(read_reference)
        reference_actions.addWidget(apply_reference)
        self.reference_status = QLabel("candidate · 仅显式测试，不加入自动状态读取")
        self.reference_status.setWordWrap(True)
        amplitude_layout.addRow("Reference Level (dBm)", self.reference_level_edit)
        amplitude_layout.addRow(reference_actions)
        amplitude_layout.addRow(self.reference_status)
        root.addWidget(amplitude_group)

        trigger_group = QGroupBox("Trigger")
        trigger_layout = QFormLayout(trigger_group)
        self.trigger_source_combo = QComboBox()
        self.trigger_source_combo.addItems(["IMMediate", "VIDeo"])
        apply_source = QPushButton("应用 Trigger Source")
        apply_source.clicked.connect(self._apply_trigger_source)
        trigger_layout.addRow("Source", self.trigger_source_combo)
        trigger_layout.addRow(apply_source)

        self.video_level_edit = QLineEdit("50")
        self.video_level_edit.setPlaceholderText("0 .. 100")
        self.trigger_offset_edit = UnitValueEdit.time(
            default_unit="ms",
            placeholder="可为负数，例如 -5",
        )
        self.trigger_offset_edit.set_base_value(0.0)
        self.trigger_slope_combo = QComboBox()
        self.trigger_slope_combo.addItems(["POSitive", "NEGative"])
        apply_video = QPushButton("应用 VIDEO Trigger")
        apply_video.clicked.connect(self._apply_video_trigger)
        self.video_status = QLabel(
            "VIDEO Trigger 使用 manual_verified 的 Source / Level / Offset / Slope；"
            "实机资格验证仍待完成。"
        )
        self.video_status.setWordWrap(True)
        trigger_layout.addRow("VIDEO Level (%)", self.video_level_edit)
        trigger_layout.addRow("Trigger Offset", self.trigger_offset_edit)
        trigger_layout.addRow("Slope", self.trigger_slope_combo)
        trigger_layout.addRow(apply_video)
        trigger_layout.addRow(self.video_status)
        root.addWidget(trigger_group)

    def _emit(self, operation_id: str, parameters: dict[str, object]) -> None:
        self.operation_requested.emit(operation_id, parameters)

    def _read_reference_level(self) -> None:
        self.reference_status.setText("正在读取 Reference Level…")
        self._emit("rohde_schwarz.fsw.read_reference_level", {})

    def _apply_reference_level(self) -> None:
        text = self.reference_level_edit.text().strip()
        if not text:
            self.reference_status.setText("请输入 Reference Level。")
            return
        try:
            value = float(text)
        except ValueError:
            self.reference_status.setText("Reference Level 必须是数字。")
            return
        self.reference_status.setText("正在设置并读回 Reference Level…")
        self._emit(
            "rohde_schwarz.fsw.set_reference_level",
            {"reference_level_dbm": value},
        )

    def _apply_trigger_source(self) -> None:
        self.video_status.setText("正在设置 Trigger Source…")
        self._emit(
            "rohde_schwarz.fsw.set_trigger_source",
            {"source": self.trigger_source_combo.currentText()},
        )

    def _apply_video_trigger(self) -> None:
        try:
            level_pct = float(self.video_level_edit.text().strip())
        except ValueError:
            self.video_status.setText("VIDEO Level 必须是数字。")
            return
        if not 0.0 <= level_pct <= 100.0:
            self.video_status.setText("VIDEO Level 必须在 0..100 %。")
            return
        try:
            offset_s = self.trigger_offset_edit.base_value_or_blank()
        except ValueError as exc:
            self.video_status.setText(f"Trigger Offset {exc}")
            return
        if offset_s == "":
            self.video_status.setText("请输入 Trigger Offset。")
            return

        self.video_status.setText("正在配置 VIDEO Trigger 并读回…")
        self._emit(
            "rohde_schwarz.fsw.configure_video_trigger",
            {
                "level_pct": level_pct,
                "offset_s": offset_s,
                "slope": self.trigger_slope_combo.currentText(),
            },
        )

    @staticmethod
    def _number(value: object) -> str:
        try:
            return f"{float(value):.12g}"
        except (TypeError, ValueError):
            return str(value)

    def handle_operation_result(
        self,
        operation_id: str,
        result: object,
        elapsed_ms: float,
    ) -> None:
        if not isinstance(result, dict):
            return

        if operation_id == "rohde_schwarz.fsw.read_reference_level":
            value = result.get("reference_level_dbm")
            if value is not None:
                self.reference_level_edit.setText(self._number(value))
            self.reference_status.setText(
                f"Reference Level 已读取 ({elapsed_ms:.0f} ms) · candidate"
            )
            return

        if operation_id == "rohde_schwarz.fsw.set_reference_level":
            readback = result.get("readback_dbm")
            if readback is not None:
                self.reference_level_edit.setText(self._number(readback))
            self.reference_status.setText(
                f"Reference Level 已设置并读回 ({elapsed_ms:.0f} ms) · candidate"
            )
            return

        if operation_id == "rohde_schwarz.fsw.set_trigger_source":
            applied = result.get("applied")
            source = None
            if isinstance(applied, dict):
                source = applied.get("source")
            if source is not None:
                index = self.trigger_source_combo.findText(str(source))
                if index >= 0:
                    self.trigger_source_combo.setCurrentIndex(index)
            self.video_status.setText(
                f"Trigger Source 已设置为 {source or '-'} ({elapsed_ms:.0f} ms)。"
            )
            return

        if operation_id == "rohde_schwarz.fsw.configure_video_trigger":
            source = str(result.get("source", "VIDeo"))
            source_upper = source.upper()
            source_text = "VIDeo" if source_upper.startswith("VID") else source
            index = self.trigger_source_combo.findText(source_text)
            if index >= 0:
                self.trigger_source_combo.setCurrentIndex(index)

            level = result.get("video_level_pct")
            if level is not None:
                self.video_level_edit.setText(self._number(level))
            offset = result.get("trigger_offset_s")
            if offset is not None:
                self.trigger_offset_edit.set_base_value(float(offset))
            slope = str(result.get("slope", ""))
            slope_text = "NEGative" if slope.upper().startswith("NEG") else "POSitive"
            slope_index = self.trigger_slope_combo.findText(slope_text)
            if slope_index >= 0:
                self.trigger_slope_combo.setCurrentIndex(slope_index)

            self.video_status.setText(
                "VIDEO Trigger 已配置并读回："
                f"Source={source}, Level={self._number(level)} %, "
                f"Offset={self._number(offset)} s, Slope={slope} "
                f"({elapsed_ms:.0f} ms)。"
            )
