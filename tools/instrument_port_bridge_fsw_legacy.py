#!/usr/bin/env python3
"""Legacy Instrument Port Bridge for older R&S FSW Windows installations.

This frontend intentionally avoids Qt/PySide.  It targets Python 3.8 + Tkinter
so it can run on Windows 7 class instrument PCs while reusing the same bridge
engines as the modern GUI.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import queue
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


ROOT = Path(__file__).resolve().parents[1]
if not getattr(sys, "frozen", False):
    core_source = ROOT / "packages" / "instrument_core" / "src"
    if core_source.is_dir():
        sys.path.insert(0, str(core_source))

from instrument_core.bridge import (  # noqa: E402
    TcpBridgeConfig,
    TcpBridgeServer,
    VisaBridgeConfig,
    VisaBridgeServer,
    list_visa_resources,
    test_tcp_instrument,
    test_visa_instrument,
)


def _settings_path() -> Path:
    base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
    if not base:
        base = str(Path.home())
    folder = Path(base) / "InstrumentAutomationPlatform" / "PortBridgeFSWLegacy"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "settings.json"


def _load_settings() -> Dict[str, Any]:
    path = _settings_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_settings(data: Dict[str, Any]) -> None:
    path = _settings_path()
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def _format_bytes(value: int) -> str:
    amount = float(value)
    for unit in ("B", "KB", "MB", "GB"):
        if amount < 1024.0 or unit == "GB":
            if unit == "B":
                return "%.0f %s" % (amount, unit)
            return "%.1f %s" % (amount, unit)
        amount /= 1024.0
    return "%d B" % value


def run_diagnostics(output_path: Optional[str] = None) -> int:
    lines = ["Instrument Port Bridge FSW Legacy diagnostics"]
    try:
        import tkinter
        import pyvisa

        lines.extend(
            [
                "status=ok",
                "python=%s" % platform.python_version(),
                "platform=%s" % platform.platform(),
                "frozen=%s" % bool(getattr(sys, "frozen", False)),
                "tk=%s" % tkinter.TkVersion,
                "pyvisa=%s" % getattr(pyvisa, "__version__", "unknown"),
                "tcp_bridge=%s" % TcpBridgeServer.__name__,
                "visa_bridge=%s" % VisaBridgeServer.__name__,
            ]
        )
        status = 0
    except Exception as exc:
        lines.extend(
            [
                "status=failed",
                "error=%s: %s" % (type(exc).__name__, exc),
            ]
        )
        status = 1

    text = "\n".join(lines) + "\n"
    if output_path:
        Path(output_path).write_text(text, encoding="utf-8")
    elif sys.stdout is not None:
        sys.stdout.write(text)
        sys.stdout.flush()
    return status


class LegacyPortBridgeApp:
    def __init__(self) -> None:
        import tkinter as tk
        from tkinter import messagebox, ttk

        self.tk = tk
        self.ttk = ttk
        self.messagebox = messagebox
        self.root = tk.Tk()
        self.root.title("Instrument Port Bridge - FSW Legacy")
        self.root.geometry("820x680")
        self.root.minsize(760, 620)

        self._bridge = None
        self._events = queue.Queue()
        self._settings = _load_settings()

        self.mode = tk.StringVar(value=self._settings.get("mode", "USB / VISA"))
        self.listen_host = tk.StringVar(value=self._settings.get("listen_host", "0.0.0.0"))
        self.listen_port = tk.StringVar(value=str(self._settings.get("listen_port", 15026)))
        self.timeout_ms = tk.StringVar(value=str(self._settings.get("timeout_ms", 5000)))
        self.remote_host = tk.StringVar(value=self._settings.get("remote_host", "127.0.0.1"))
        self.remote_port = tk.StringVar(value=str(self._settings.get("remote_port", 5025)))
        self.visa_resource = tk.StringVar(value=self._settings.get("visa_resource", ""))
        self.visa_backend = tk.StringVar(value=self._settings.get("visa_backend", ""))
        self.status = tk.StringVar(value="已停止")
        self.client = tk.StringVar(value="-")
        self.traffic = tk.StringVar(value="RX 0 B / TX 0 B")
        self.duration = tk.StringVar(value="-")

        self._build_ui()
        self._mode_changed()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._poll_events)
        self.root.after(500, self._refresh_stats)

    def _build_ui(self) -> None:
        ttk = self.ttk
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)

        title = ttk.Label(
            outer,
            text="Instrument Port Bridge / FSW Legacy",
            font=("Segoe UI", 15, "bold"),
        )
        title.pack(anchor="w")
        ttk.Label(
            outer,
            text=(
                "面向老款 R&S FSW Windows 仪表。无 Qt 依赖；支持 TCP→TCP 与 "
                "USB/VISA→TCP。每个监听端口默认单客户端独占。"
            ),
            wraplength=760,
        ).pack(anchor="w", pady=(4, 10))

        config = ttk.LabelFrame(outer, text="桥接配置", padding=10)
        config.pack(fill="x")
        config.columnconfigure(1, weight=1)

        ttk.Label(config, text="连接类型").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.mode_combo = ttk.Combobox(
            config,
            textvariable=self.mode,
            values=("Network / TCP", "USB / VISA"),
            state="readonly",
        )
        self.mode_combo.grid(row=0, column=1, sticky="ew", pady=4)
        self.mode_combo.bind("<<ComboboxSelected>>", lambda _event: self._mode_changed())

        ttk.Label(config, text="本地监听地址").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(config, textvariable=self.listen_host).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(config, text="本地监听端口").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(config, textvariable=self.listen_port).grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(config, text="超时 (ms)").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(config, textvariable=self.timeout_ms).grid(row=3, column=1, sticky="ew", pady=4)

        self.network_frame = ttk.LabelFrame(outer, text="Network / TCP 仪表", padding=10)
        self.network_frame.columnconfigure(1, weight=1)
        ttk.Label(self.network_frame, text="仪表 IP / 主机名").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(self.network_frame, textvariable=self.remote_host).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(self.network_frame, text="仪表 TCP 端口").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(self.network_frame, textvariable=self.remote_port).grid(row=1, column=1, sticky="ew", pady=4)

        self.visa_frame = ttk.LabelFrame(outer, text="USB / VISA 仪表", padding=10)
        self.visa_frame.columnconfigure(1, weight=1)
        ttk.Label(self.visa_frame, text="VISA Resource").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        resource_row = ttk.Frame(self.visa_frame)
        resource_row.grid(row=0, column=1, sticky="ew", pady=4)
        resource_row.columnconfigure(0, weight=1)
        self.resource_combo = ttk.Combobox(resource_row, textvariable=self.visa_resource)
        self.resource_combo.grid(row=0, column=0, sticky="ew")
        self.scan_button = ttk.Button(resource_row, text="扫描 VISA", command=self._scan_visa)
        self.scan_button.grid(row=0, column=1, padx=(8, 0))
        ttk.Label(self.visa_frame, text="VISA Backend").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(self.visa_frame, textvariable=self.visa_backend).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Label(
            self.visa_frame,
            text="建议留空，优先使用 FSW 本机已有的 R&S/NI/Keysight VISA Runtime。",
        ).grid(row=2, column=1, sticky="w", pady=(0, 4))

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=10)
        self.test_button = ttk.Button(actions, text="连接测试 (*IDN?)", command=self._test_connection)
        self.test_button.pack(side="left")
        self.start_button = ttk.Button(actions, text="启动转发", command=self._start_bridge)
        self.start_button.pack(side="left", padx=(8, 0))
        self.stop_button = ttk.Button(actions, text="停止", command=self._stop_bridge, state="disabled")
        self.stop_button.pack(side="left", padx=(8, 0))

        status_box = ttk.LabelFrame(outer, text="运行状态", padding=10)
        status_box.pack(fill="x")
        status_box.columnconfigure(1, weight=1)
        for row, (label, variable) in enumerate(
            (
                ("状态", self.status),
                ("客户端", self.client),
                ("流量", self.traffic),
                ("连接时长", self.duration),
            )
        ):
            ttk.Label(status_box, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=2)
            ttk.Label(status_box, textvariable=variable).grid(row=row, column=1, sticky="w", pady=2)

        log_box = ttk.LabelFrame(outer, text="日志", padding=8)
        log_box.pack(fill="both", expand=True, pady=(10, 0))
        self.log = self.tk.Text(log_box, height=12, wrap="word", state="disabled")
        scroll = ttk.Scrollbar(log_box, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _mode_changed(self) -> None:
        self.network_frame.pack_forget()
        self.visa_frame.pack_forget()
        if self.mode.get() == "Network / TCP":
            self.network_frame.pack(fill="x", pady=(10, 0), before=self._actions_widget())
            if self.listen_port.get() in ("", "15026"):
                self.listen_port.set(str(self._settings.get("network_listen_port", 15025)))
        else:
            self.visa_frame.pack(fill="x", pady=(10, 0), before=self._actions_widget())
            if self.listen_port.get() in ("", "15025"):
                self.listen_port.set(str(self._settings.get("usb_listen_port", 15026)))

    def _actions_widget(self):
        return self.test_button.master

    def _parse_int(self, value: str, label: str, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except ValueError:
            raise ValueError("%s 必须是整数" % label)
        if parsed < minimum or parsed > maximum:
            raise ValueError("%s 必须在 %d..%d 范围内" % (label, minimum, maximum))
        return parsed

    def _scan_visa(self) -> None:
        self.scan_button.configure(state="disabled")
        self._append_log("正在扫描 VISA 资源...")
        backend = self.visa_backend.get().strip() or None

        def worker() -> None:
            try:
                values = list_visa_resources(backend)
                self._events.put(("scan", True, values))
            except Exception as exc:
                self._events.put(("scan", False, str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _test_connection(self) -> None:
        self.test_button.configure(state="disabled")
        self._append_log("开始 *IDN? 连接测试...")
        mode = self.mode.get()
        try:
            timeout = self._parse_int(self.timeout_ms.get(), "超时", 100, 120000)
            remote_port = self._parse_int(self.remote_port.get(), "仪表 TCP 端口", 1, 65535)
        except Exception as exc:
            self.test_button.configure(state="normal")
            self.messagebox.showwarning("参数错误", str(exc))
            return

        def worker() -> None:
            try:
                if mode == "Network / TCP":
                    result = test_tcp_instrument(
                        self.remote_host.get().strip(),
                        remote_port,
                        timeout_s=timeout / 1000.0,
                    )
                else:
                    resource = self.visa_resource.get().strip()
                    if not resource:
                        raise ValueError("请先扫描或输入 VISA Resource")
                    result = test_visa_instrument(
                        resource,
                        timeout_ms=timeout,
                        backend=self.visa_backend.get().strip() or None,
                    )
                self._events.put(("test", True, result or "连接成功，但返回为空"))
            except Exception as exc:
                self._events.put(("test", False, str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _start_bridge(self) -> None:
        if self._bridge is not None:
            return
        try:
            listen_port = self._parse_int(self.listen_port.get(), "本地监听端口", 1, 65535)
            timeout = self._parse_int(self.timeout_ms.get(), "超时", 100, 120000)
            listen_host = self.listen_host.get().strip()
            if not listen_host:
                raise ValueError("本地监听地址不能为空")

            if self.mode.get() == "Network / TCP":
                remote_port = self._parse_int(self.remote_port.get(), "仪表 TCP 端口", 1, 65535)
                bridge = TcpBridgeServer(
                    TcpBridgeConfig(
                        listen_host=listen_host,
                        listen_port=listen_port,
                        remote_host=self.remote_host.get().strip(),
                        remote_port=remote_port,
                        connect_timeout_s=timeout / 1000.0,
                    ),
                    on_event=self._queue_log,
                )
            else:
                resource = self.visa_resource.get().strip()
                if not resource:
                    raise ValueError("请先扫描或输入 VISA Resource")
                bridge = VisaBridgeServer(
                    VisaBridgeConfig(
                        resource=resource,
                        listen_host=listen_host,
                        listen_port=listen_port,
                        timeout_ms=timeout,
                        backend=self.visa_backend.get().strip() or None,
                    ),
                    on_event=self._queue_log,
                )

            bridge.start()
            self._bridge = bridge
            self.status.set("运行中")
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.mode_combo.configure(state="disabled")
            self._save_current_settings()
        except Exception as exc:
            self._bridge = None
            self._append_log("启动失败: %s" % exc)
            self.messagebox.showerror("启动失败", str(exc))

    def _stop_bridge(self) -> None:
        bridge = self._bridge
        self._bridge = None
        if bridge is not None:
            try:
                bridge.stop()
            except Exception as exc:
                self._append_log("停止时发生错误: %s" % exc)
        self.status.set("已停止")
        self.client.set("-")
        self.duration.set("-")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.mode_combo.configure(state="readonly")

    def _queue_log(self, message: str) -> None:
        self._events.put(("log", message))

    def _append_log(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log.configure(state="normal")
        self.log.insert("end", "[%s] %s\n" % (stamp, message))
        self.log.see("end")
        self.log.configure(state="disabled")

    def _poll_events(self) -> None:
        while True:
            try:
                event = self._events.get_nowait()
            except queue.Empty:
                break
            kind = event[0]
            if kind == "log":
                self._append_log(event[1])
            elif kind == "scan":
                self.scan_button.configure(state="normal")
                ok, payload = event[1], event[2]
                if ok:
                    values = list(payload)
                    self.resource_combo["values"] = values
                    if values and not self.visa_resource.get().strip():
                        self.visa_resource.set(values[0])
                    self._append_log("扫描到 %d 个 VISA 资源" % len(values))
                else:
                    self._append_log("VISA 扫描失败: %s" % payload)
                    self.messagebox.showwarning("VISA 扫描失败", str(payload))
            elif kind == "test":
                self.test_button.configure(state="normal")
                ok, text = event[1], event[2]
                if ok:
                    self._append_log("*IDN? 成功: %s" % text)
                    self.messagebox.showinfo("连接成功", str(text))
                else:
                    self._append_log("连接测试失败: %s" % text)
                    self.messagebox.showwarning("连接失败", str(text))
        self.root.after(100, self._poll_events)

    def _refresh_stats(self) -> None:
        bridge = self._bridge
        if bridge is not None:
            try:
                snapshot = bridge.snapshot()
                self.status.set("运行中" if snapshot.running else "已停止")
                self.client.set(snapshot.client_address or "等待客户端")
                self.traffic.set(
                    "RX %s / TX %s"
                    % (
                        _format_bytes(snapshot.bytes_from_client),
                        _format_bytes(snapshot.bytes_to_client),
                    )
                )
                if snapshot.connected_seconds is None:
                    self.duration.set("-")
                else:
                    seconds = int(snapshot.connected_seconds)
                    self.duration.set(
                        "%02d:%02d:%02d"
                        % (seconds // 3600, (seconds % 3600) // 60, seconds % 60)
                    )
            except Exception as exc:
                self._append_log("状态刷新失败: %s" % exc)
        self.root.after(500, self._refresh_stats)

    def _save_current_settings(self) -> None:
        listen_port = self.listen_port.get()
        data = {
            "mode": self.mode.get(),
            "listen_host": self.listen_host.get().strip(),
            "listen_port": int(listen_port) if listen_port.isdigit() else listen_port,
            "timeout_ms": int(self.timeout_ms.get()) if self.timeout_ms.get().isdigit() else self.timeout_ms.get(),
            "remote_host": self.remote_host.get().strip(),
            "remote_port": int(self.remote_port.get()) if self.remote_port.get().isdigit() else self.remote_port.get(),
            "visa_resource": self.visa_resource.get().strip(),
            "visa_backend": self.visa_backend.get().strip(),
        }
        if self.mode.get() == "Network / TCP":
            data["network_listen_port"] = data["listen_port"]
            data["usb_listen_port"] = self._settings.get("usb_listen_port", 15026)
        else:
            data["usb_listen_port"] = data["listen_port"]
            data["network_listen_port"] = self._settings.get("network_listen_port", 15025)
        self._settings = data
        _save_settings(data)

    def _on_close(self) -> None:
        try:
            self._save_current_settings()
        finally:
            self._stop_bridge()
            self.root.destroy()

    def run(self) -> int:
        self.root.mainloop()
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Instrument Port Bridge FSW Legacy")
    parser.add_argument("--diagnostics", action="store_true")
    parser.add_argument("--diagnostics-file", default=None)
    args = parser.parse_args()
    if args.diagnostics or args.diagnostics_file:
        return run_diagnostics(args.diagnostics_file)
    return LegacyPortBridgeApp().run()


if __name__ == "__main__":
    raise SystemExit(main())
