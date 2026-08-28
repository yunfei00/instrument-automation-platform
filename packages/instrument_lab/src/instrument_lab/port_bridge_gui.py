"""PySide6 GUI for Instrument Port Bridge."""

from __future__ import annotations

import threading
from datetime import datetime

from PySide6.QtCore import QSettings, QTimer, QObject, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from instrument_core.bridge import (
    TcpBridgeConfig,
    TcpBridgeServer,
    VisaBridgeConfig,
    VisaBridgeServer,
    list_visa_resources,
    test_tcp_instrument,
    test_visa_instrument,
)


class _Signals(QObject):
    log = Signal(str)
    test_finished = Signal(bool, str)
    scan_finished = Signal(object, str)


class PortBridgeWindow(QMainWindow):
    """Single-window GUI for USB/VISA and TCP instrument forwarding."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Instrument Port Bridge - 仪表端口桥接")
        self.resize(900, 680)

        self._settings = QSettings(
            "InstrumentAutomationPlatform",
            "InstrumentPortBridge",
        )
        self._signals = _Signals()
        self._signals.log.connect(self._append_log)
        self._signals.test_finished.connect(self._on_test_finished)
        self._signals.scan_finished.connect(self._on_scan_finished)
        self._bridge: TcpBridgeServer | VisaBridgeServer | None = None

        self._build_ui()
        self._load_settings()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_stats)
        self._timer.start(500)

    def _build_ui(self) -> None:
        root = QWidget(self)
        layout = QVBoxLayout(root)

        title = QLabel("Instrument Port Bridge / 仪表端口桥接工具")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(title)

        note = QLabel(
            "支持 Network TCP → TCP 原始字节流转发，以及 USB/VISA → TCP SCPI 消息桥接。"
            " 每个桥接端口默认只允许一个客户端独占仪表。"
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        common = QGroupBox("桥接配置")
        common_form = QFormLayout(common)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Network / TCP", "USB / VISA"])
        self.mode_combo.currentIndexChanged.connect(self._mode_changed)
        common_form.addRow("连接类型", self.mode_combo)

        self.listen_host_edit = QLineEdit("0.0.0.0")
        common_form.addRow("本地监听地址", self.listen_host_edit)

        self.listen_port_spin = QSpinBox()
        self.listen_port_spin.setRange(1, 65535)
        self.listen_port_spin.setValue(15025)
        common_form.addRow("本地监听端口", self.listen_port_spin)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(100, 120000)
        self.timeout_spin.setSingleStep(500)
        self.timeout_spin.setValue(5000)
        self.timeout_spin.setSuffix(" ms")
        common_form.addRow("连接 / VISA 超时", self.timeout_spin)
        layout.addWidget(common)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_network_page())
        self.stack.addWidget(self._build_usb_page())
        layout.addWidget(self.stack)

        actions = QHBoxLayout()
        self.test_button = QPushButton("连接测试 (*IDN?)")
        self.test_button.clicked.connect(self._test_connection)
        self.start_button = QPushButton("启动转发")
        self.start_button.clicked.connect(self._start_bridge)
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self._stop_bridge)
        self.stop_button.setEnabled(False)
        actions.addWidget(self.test_button)
        actions.addWidget(self.start_button)
        actions.addWidget(self.stop_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        status_group = QGroupBox("运行状态")
        status_form = QFormLayout(status_group)
        self.status_label = QLabel("已停止")
        self.client_label = QLabel("-")
        self.traffic_label = QLabel("RX 0 B / TX 0 B")
        self.duration_label = QLabel("-")
        status_form.addRow("状态", self.status_label)
        status_form.addRow("客户端", self.client_label)
        status_form.addRow("流量", self.traffic_label)
        status_form.addRow("连接时长", self.duration_label)
        layout.addWidget(status_group)

        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout(log_group)
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        log_layout.addWidget(self.log_edit)
        layout.addWidget(log_group, 1)

        self.setCentralWidget(root)

    def _build_network_page(self) -> QWidget:
        page = QGroupBox("Network / TCP 仪表")
        form = QFormLayout(page)
        self.remote_host_edit = QLineEdit("192.168.1.100")
        self.remote_port_spin = QSpinBox()
        self.remote_port_spin.setRange(1, 65535)
        self.remote_port_spin.setValue(5025)
        form.addRow("仪表 IP / 主机名", self.remote_host_edit)
        form.addRow("仪表 TCP 端口", self.remote_port_spin)
        return page

    def _build_usb_page(self) -> QWidget:
        page = QGroupBox("USB / VISA 仪表")
        form = QFormLayout(page)

        resource_row = QHBoxLayout()
        self.resource_combo = QComboBox()
        self.resource_combo.setEditable(True)
        self.scan_button = QPushButton("扫描 VISA")
        self.scan_button.clicked.connect(self._scan_visa)
        resource_row.addWidget(self.resource_combo, 1)
        resource_row.addWidget(self.scan_button)
        form.addRow("VISA Resource", resource_row)

        self.backend_edit = QLineEdit()
        self.backend_edit.setPlaceholderText(
            "留空=系统默认 VISA；@py=PyVISA-py（可选）"
        )
        form.addRow("VISA Backend", self.backend_edit)
        return page

    def _mode_changed(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.listen_port_spin.setValue(
                int(self._settings.value("network_listen_port", 15025))
            )
        else:
            self.listen_port_spin.setValue(
                int(self._settings.value("usb_listen_port", 15026))
            )

    def _scan_visa(self) -> None:
        self.scan_button.setEnabled(False)
        self._append_log("正在扫描 VISA 资源...")
        backend = self.backend_edit.text().strip() or None

        def worker() -> None:
            try:
                resources = list_visa_resources(backend)
                self._signals.scan_finished.emit(resources, "")
            except Exception as exc:
                self._signals.scan_finished.emit([], str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_scan_finished(self, resources: object, error: str) -> None:
        self.scan_button.setEnabled(True)
        if error:
            self._append_log(f"VISA 扫描失败: {error}")
            QMessageBox.warning(self, "VISA 扫描失败", error)
            return

        values = [str(item) for item in resources]
        current = self.resource_combo.currentText().strip()
        self.resource_combo.clear()
        self.resource_combo.addItems(values)
        if current and current not in values:
            self.resource_combo.insertItem(0, current)
            self.resource_combo.setCurrentIndex(0)
        self._append_log(f"扫描到 {len(values)} 个 VISA 资源")

    def _test_connection(self) -> None:
        self.test_button.setEnabled(False)
        self._append_log("开始 *IDN? 连接测试...")
        mode = self.mode_combo.currentIndex()
        timeout_ms = self.timeout_spin.value()

        def worker() -> None:
            try:
                if mode == 0:
                    result = test_tcp_instrument(
                        self.remote_host_edit.text().strip(),
                        self.remote_port_spin.value(),
                        timeout_s=timeout_ms / 1000.0,
                    )
                else:
                    resource = self.resource_combo.currentText().strip()
                    if not resource:
                        raise ValueError("请先选择或输入 VISA Resource")
                    result = test_visa_instrument(
                        resource,
                        timeout_ms=timeout_ms,
                        backend=self.backend_edit.text().strip() or None,
                    )
                self._signals.test_finished.emit(True, result or "连接成功，但返回为空")
            except Exception as exc:
                self._signals.test_finished.emit(False, str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_test_finished(self, ok: bool, text: str) -> None:
        self.test_button.setEnabled(True)
        if ok:
            self._append_log(f"*IDN? 成功: {text}")
            QMessageBox.information(self, "连接成功", text)
        else:
            self._append_log(f"连接测试失败: {text}")
            QMessageBox.warning(self, "连接失败", text)

    def _start_bridge(self) -> None:
        if self._bridge is not None:
            return

        try:
            listen_host = self.listen_host_edit.text().strip()
            listen_port = self.listen_port_spin.value()
            timeout_ms = self.timeout_spin.value()

            if self.mode_combo.currentIndex() == 0:
                config = TcpBridgeConfig(
                    listen_host=listen_host,
                    listen_port=listen_port,
                    remote_host=self.remote_host_edit.text().strip(),
                    remote_port=self.remote_port_spin.value(),
                    connect_timeout_s=timeout_ms / 1000.0,
                )
                bridge: TcpBridgeServer | VisaBridgeServer = TcpBridgeServer(
                    config,
                    on_event=self._signals.log.emit,
                )
            else:
                resource = self.resource_combo.currentText().strip()
                if not resource:
                    raise ValueError("请先选择或输入 VISA Resource")
                config = VisaBridgeConfig(
                    resource=resource,
                    listen_host=listen_host,
                    listen_port=listen_port,
                    timeout_ms=timeout_ms,
                    backend=self.backend_edit.text().strip() or None,
                )
                bridge = VisaBridgeServer(
                    config,
                    on_event=self._signals.log.emit,
                )

            bridge.start()
            self._bridge = bridge
            self._save_settings()
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.mode_combo.setEnabled(False)
            self.status_label.setText("运行中")
        except Exception as exc:
            self._bridge = None
            self._append_log(f"启动失败: {exc}")
            QMessageBox.critical(self, "启动失败", str(exc))

    def _stop_bridge(self) -> None:
        bridge = self._bridge
        self._bridge = None
        if bridge is not None:
            bridge.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.mode_combo.setEnabled(True)
        self.status_label.setText("已停止")
        self.client_label.setText("-")
        self.duration_label.setText("-")

    def _refresh_stats(self) -> None:
        bridge = self._bridge
        if bridge is None:
            return
        snapshot = bridge.snapshot()
        self.status_label.setText("运行中" if snapshot.running else "已停止")
        self.client_label.setText(snapshot.client_address or "等待客户端")
        self.traffic_label.setText(
            f"RX {self._format_bytes(snapshot.bytes_from_client)} / "
            f"TX {self._format_bytes(snapshot.bytes_to_client)}"
        )
        if snapshot.connected_seconds is None:
            self.duration_label.setText("-")
        else:
            seconds = int(snapshot.connected_seconds)
            self.duration_label.setText(
                f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"
            )

    def _append_log(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log_edit.append(f"[{stamp}] {message}")

    def _load_settings(self) -> None:
        mode = int(self._settings.value("mode", 0))
        self.mode_combo.setCurrentIndex(0 if mode not in (0, 1) else mode)
        self.listen_host_edit.setText(
            str(self._settings.value("listen_host", "0.0.0.0"))
        )
        self.remote_host_edit.setText(
            str(self._settings.value("remote_host", "192.168.1.100"))
        )
        self.remote_port_spin.setValue(
            int(self._settings.value("remote_port", 5025))
        )
        self.timeout_spin.setValue(int(self._settings.value("timeout_ms", 5000)))
        saved_resource = str(self._settings.value("visa_resource", ""))
        if saved_resource:
            self.resource_combo.addItem(saved_resource)
        self.backend_edit.setText(str(self._settings.value("visa_backend", "")))
        self._mode_changed(self.mode_combo.currentIndex())

    def _save_settings(self) -> None:
        mode = self.mode_combo.currentIndex()
        self._settings.setValue("mode", mode)
        self._settings.setValue("listen_host", self.listen_host_edit.text().strip())
        self._settings.setValue("remote_host", self.remote_host_edit.text().strip())
        self._settings.setValue("remote_port", self.remote_port_spin.value())
        self._settings.setValue("timeout_ms", self.timeout_spin.value())
        self._settings.setValue("visa_resource", self.resource_combo.currentText().strip())
        self._settings.setValue("visa_backend", self.backend_edit.text().strip())
        key = "network_listen_port" if mode == 0 else "usb_listen_port"
        self._settings.setValue(key, self.listen_port_spin.value())
        self._settings.sync()

    @staticmethod
    def _format_bytes(value: int) -> str:
        amount = float(value)
        for unit in ("B", "KB", "MB", "GB"):
            if amount < 1024.0 or unit == "GB":
                return f"{amount:.0f} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
            amount /= 1024.0
        return f"{value} B"

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        self._save_settings()
        self._stop_bridge()
        super().closeEvent(event)


def run_port_bridge_gui() -> int:
    app = QApplication.instance() or QApplication([])
    window = PortBridgeWindow()
    window.show()
    return app.exec()
