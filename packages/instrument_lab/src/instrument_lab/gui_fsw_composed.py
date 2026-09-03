"""Composition wrapper for the FSW dedicated control surface.

The main trace/control panel remains isolated from qualification controls and from
binary screenshot rendering.  Each large surface gets its own tab so the FSW UI
stays spacious as capabilities grow.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from .gui_fsw import FSWControlPanel
from .gui_fsw_reference_trigger import FSWReferenceTriggerControls
from .gui_fsw_screenshot import FSWScreenshotPanel


class FSWComposedPanel(QWidget):
    """FSW main console plus amplitude/trigger and instrument-screen pages."""

    operation_requested = Signal(str, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget(self)
        self.main_panel = FSWControlPanel(self.tabs)
        self.screenshot_panel = FSWScreenshotPanel(self.tabs)
        self.reference_trigger_panel = FSWReferenceTriggerControls(self.tabs)

        self.main_panel.operation_requested.connect(self.operation_requested.emit)
        self.screenshot_panel.operation_requested.connect(self.operation_requested.emit)
        self.reference_trigger_panel.operation_requested.connect(
            self.operation_requested.emit
        )

        self.tabs.addTab(self.main_panel, "主控制台")
        self.tabs.addTab(self.screenshot_panel, "Instrument Screen")
        self.tabs.addTab(self.reference_trigger_panel, "幅度 / Trigger")
        layout.addWidget(self.tabs, 1)

    def handle_operation_result(
        self,
        operation_id: str,
        result: object,
        elapsed_ms: float,
    ) -> None:
        self.main_panel.handle_operation_result(operation_id, result, elapsed_ms)
        self.screenshot_panel.handle_operation_result(
            operation_id,
            result,
            elapsed_ms,
        )
        self.reference_trigger_panel.handle_operation_result(
            operation_id,
            result,
            elapsed_ms,
        )
