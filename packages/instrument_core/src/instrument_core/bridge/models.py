"""Configuration and thread-safe statistics for instrument bridges."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import monotonic


@dataclass
class TcpBridgeConfig:
    listen_host: str = "0.0.0.0"
    listen_port: int = 15025
    remote_host: str = "127.0.0.1"
    remote_port: int = 5025
    connect_timeout_s: float = 5.0
    recv_size: int = 65536

    def validate(self) -> None:
        _validate_common(self.listen_host, self.listen_port, self.recv_size)
        if not self.remote_host.strip():
            raise ValueError("remote_host must not be empty")
        _validate_port("remote_port", self.remote_port)
        if self.connect_timeout_s <= 0:
            raise ValueError("connect_timeout_s must be greater than zero")


@dataclass
class VisaBridgeConfig:
    resource: str
    listen_host: str = "0.0.0.0"
    listen_port: int = 15026
    timeout_ms: int = 5000
    recv_size: int = 65536
    backend: str | None = None

    def validate(self) -> None:
        _validate_common(self.listen_host, self.listen_port, self.recv_size)
        if not self.resource.strip():
            raise ValueError("VISA resource must not be empty")
        if self.timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")


def _validate_common(host: str, port: int, recv_size: int) -> None:
    if not host.strip():
        raise ValueError("listen_host must not be empty")
    _validate_port("listen_port", port)
    if recv_size < 1024:
        raise ValueError("recv_size must be at least 1024 bytes")


def _validate_port(name: str, value: int) -> None:
    if not 1 <= int(value) <= 65535:
        raise ValueError(f"{name} must be between 1 and 65535")


@dataclass(frozen=True)
class BridgeStatsSnapshot:
    bytes_from_client: int
    bytes_to_client: int
    client_address: str | None
    connected_seconds: float | None
    running: bool


class BridgeStats:
    """Small thread-safe counter object shared by both bridge engines."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._bytes_from_client = 0
        self._bytes_to_client = 0
        self._client_address: str | None = None
        self._connected_at: float | None = None
        self._running = False

    def set_running(self, running: bool) -> None:
        with self._lock:
            self._running = running

    def client_connected(self, address: str) -> None:
        with self._lock:
            self._client_address = address
            self._connected_at = monotonic()

    def client_disconnected(self) -> None:
        with self._lock:
            self._client_address = None
            self._connected_at = None

    def add_from_client(self, count: int) -> None:
        with self._lock:
            self._bytes_from_client += max(0, count)

    def add_to_client(self, count: int) -> None:
        with self._lock:
            self._bytes_to_client += max(0, count)

    def snapshot(self) -> BridgeStatsSnapshot:
        with self._lock:
            connected_seconds = None
            if self._connected_at is not None:
                connected_seconds = max(0.0, monotonic() - self._connected_at)
            return BridgeStatsSnapshot(
                bytes_from_client=self._bytes_from_client,
                bytes_to_client=self._bytes_to_client,
                client_address=self._client_address,
                connected_seconds=connected_seconds,
                running=self._running,
            )
