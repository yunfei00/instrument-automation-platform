"""Qt-only FSW Instrument Screen page.

The widget owns only presentation and local file saving. Screenshot acquisition is
performed by the registered Instrument Operation so VISA/SCPI remain below Qt.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QResizeEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .fsw_screenshot_operation import ensure_fsw_screenshot_operation_registered


ensure_fsw_screenshot_operation_registered()


class _AspectScreenshotLabel(QLabel):
    """Large screenshot surface that rescales without distorting aspect ratio."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._source = QPixmap()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(640, 400)
        self.setStyleSheet(
            "QLabel { border: 1px solid #666; background: #111; color: #ddd; }"
        )
        self.setText("尚未读取 FSW 仪表截图。")

    def set_source_pixmap(self, pixmap: QPixmap) -> None:
        self._source = pixmap
        self._refresh_scaled()

    def _refresh_scaled(self) -> None:
        if self._source.isNull():
            return
        target = self.contentsRect().size()
        if target.width() <= 1 or target.height() <= 1:
            return
        self.setPixmap(
            self._source.scaled(
                target,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        self._refresh_scaled()


class FSWScreenshotPanel(QWidget):
    """Large FSW screenshot page kept separate from parameter controls."""

    operation_requested = Signal(str, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._last_data = b""
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        title = QLabel("R&S FSW · Instrument Screen")
        title.setStyleSheet("font-weight: 600; font-size: 17px;")
        root.addWidget(title)

        note = QLabel(
            "读取当前 FSW 测量屏幕 PNG。截图与 Trace Data View 分开显示，"
            "避免参数控件挤占图像区域。"
        )
        note.setWordWrap(True)
        root.addWidget(note)

        actions = QHBoxLayout()
        refresh = QPushButton("刷新截图")
        refresh.clicked.connect(self._capture)
        actions.addWidget(refresh)
        self.save_button = QPushButton("保存截图")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self._save)
        actions.addWidget(self.save_button)
        actions.addStretch(1)
        root.addLayout(actions)

        self.screen = _AspectScreenshotLabel(self)
        root.addWidget(self.screen, 1)

        self.status = QLabel("Screenshot：尚未读取")
        self.status.setWordWrap(True)
        root.addWidget(self.status)

    def _capture(self) -> None:
        self.status.setText("Screenshot：正在读取…")
        self.operation_requested.emit("rohde_schwarz.fsw.screenshot", {})

    def _save(self) -> None:
        if not self._last_data:
            return
        filename, _selected = QFileDialog.getSaveFileName(
            self,
            "保存 FSW Screenshot",
            "fsw_screenshot.png",
            "PNG Files (*.png)",
        )
        if not filename:
            return
        path = Path(filename)
        if path.suffix.lower() != ".png":
            path = path.with_suffix(".png")
        path.write_bytes(self._last_data)
        self.status.setText(f"Screenshot：已保存 {path.name}")

    def handle_operation_result(
        self,
        operation_id: str,
        result: object,
        elapsed_ms: float,
    ) -> None:
        if operation_id != "rohde_schwarz.fsw.screenshot":
            return
        if not isinstance(result, dict):
            return

        data = result.get("data")
        if not isinstance(data, (bytes, bytearray, memoryview)):
            self.status.setText("Screenshot：返回结构缺少 PNG 数据。")
            return

        payload = bytes(data)
        pixmap = QPixmap()
        if not pixmap.loadFromData(payload, "PNG"):
            self.status.setText("Screenshot：PNG 数据无法由 Qt 解码。")
            return

        self._last_data = payload
        self.screen.set_source_pixmap(pixmap)
        self.save_button.setEnabled(True)

        cleanup_error = result.get("cleanup_error")
        message = (
            f"Screenshot：PNG / {len(payload)} bytes / {elapsed_ms:.0f} ms"
        )
        if cleanup_error:
            message += f"；仪表临时文件清理失败：{cleanup_error}"
        self.status.setText(message)
