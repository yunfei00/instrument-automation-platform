"""Composition wrapper for the FSW dedicated control surface.

The hardware-verified/main FSW panel remains untouched.  New amplitude/trigger
qualification controls live on a sibling tab so the screen stays spacious and a
candidate command cannot destabilize the primary Trace Data View.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from .gui_fsw import FSWControlPanel
from .gui_fsw_reference_trigger import FSWReferenceTriggerControls


class FSWComposedPanel(QWidget):
    """FSW main console plus isolated amplitude/trigger qualification page."""

    operation_requested = Signal(str, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget(self)
        self.main_panel = FSWControlPanel(self.tabs)
        self.reference_trigger_panel = FSWReferenceTriggerControls(self.tabs)

        self.main_panel.operation_requested.connect(self.operation_requested.emit)
        self.reference_trigger_panel.operation_requested.connect(
            self.operation_requested.emit
        )

        self.tabs.addTab(self.main_panel, "主控制台")
        self.tabs.addTab(self.reference_trigger_panel, "幅度 / Trigger")
        layout.addWidget(self.tabs, 1)

    def handle_operation_result(
        self,
        operation_id: str,
        result: object,
        elapsed_ms: float,
    ) -> None:
        self.main_panel.handle_operation_result(operation_id, result, elapsed_ms)
        self.reference_trigger_panel.handle_operation_result(
            operation_id,
            result,
            elapsed_ms,
        )
