"""Instrument discovery and connection-test helpers for bridge UIs."""

from __future__ import annotations

import socket

from instrument_core.transport.base import TransportConfig
from instrument_core.transport.visa import VisaTransport


def list_visa_resources(backend: str | None = None) -> list[str]:
    import pyvisa

    manager = pyvisa.ResourceManager(backend) if backend else pyvisa.ResourceManager()
    try:
        resources = list(manager.list_resources())
    finally:
        manager.close()
    return sorted(resources, key=lambda item: (not item.upper().startswith("USB"), item))


def test_tcp_instrument(
    host: str,
    port: int,
    *,
    timeout_s: float = 5.0,
    command: bytes = b"*IDN?\n",
) -> str:
    with socket.create_connection((host, port), timeout=timeout_s) as sock:
        sock.settimeout(timeout_s)
        sock.sendall(command)
        chunks: list[bytes] = []
        total = 0
        while total < 65536:
            data = sock.recv(4096)
            if not data:
                break
            chunks.append(data)
            total += len(data)
            if b"\n" in data:
                break
        return b"".join(chunks).decode("utf-8", errors="replace").strip()


def test_visa_instrument(
    resource: str,
    *,
    timeout_ms: int = 5000,
    backend: str | None = None,
) -> str:
    transport = VisaTransport(
        TransportConfig(
            resource=resource,
            timeout_ms=timeout_ms,
            read_termination="\n",
            write_termination="\n",
        ),
        backend=backend or None,
    )
    transport.open()
    try:
        return transport.query("*IDN?").strip()
    finally:
        transport.close()
