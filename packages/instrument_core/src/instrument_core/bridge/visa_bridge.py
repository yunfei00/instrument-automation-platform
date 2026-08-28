"""VISA/USBTMC-to-TCP SCPI bridge."""

from __future__ import annotations

import socket
import threading
from collections.abc import Callable

from instrument_core.transport.base import TransportConfig
from instrument_core.transport.visa import VisaTransport

from .models import BridgeStats, BridgeStatsSnapshot, VisaBridgeConfig
from .protocol import ScpiLineFramer, is_scpi_query

EventCallback = Callable[[str], None]


class VisaBridgeServer:
    """Expose a VISA instrument through a local TCP socket.

    This is a SCPI message bridge, not USB-over-IP. TCP requests are framed by
    newline, sent to VISA as raw bytes, and query responses are returned with
    ``read_raw`` so binary IEEE 488.2 blocks are preserved.
    """

    def __init__(
        self,
        config: VisaBridgeConfig,
        *,
        on_event: EventCallback | None = None,
    ) -> None:
        config.validate()
        self.config = config
        self._on_event = on_event
        self._stop = threading.Event()
        self._listener: socket.socket | None = None
        self._client: socket.socket | None = None
        self._accept_thread: threading.Thread | None = None
        self._session_lock = threading.Lock()
        self.stats = BridgeStats()

    @property
    def is_running(self) -> bool:
        return self.stats.snapshot().running

    def snapshot(self) -> BridgeStatsSnapshot:
        return self.stats.snapshot()

    def start(self) -> None:
        if self.is_running:
            return

        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.config.listen_host, self.config.listen_port))
        listener.listen(4)
        listener.settimeout(0.5)

        self._listener = listener
        self._stop.clear()
        self.stats.set_running(True)
        self._accept_thread = threading.Thread(
            target=self._accept_loop,
            name="instrument-visa-bridge-accept",
            daemon=True,
        )
        self._accept_thread.start()
        self._emit(
            f"VISA bridge listening on {self.config.listen_host}:"
            f"{self.config.listen_port} -> {self.config.resource}"
        )

    def stop(self) -> None:
        self._stop.set()
        self._close_socket(self._listener)
        self._close_socket(self._client)
        self._listener = None
        self._client = None
        self.stats.client_disconnected()
        self.stats.set_running(False)
        thread = self._accept_thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1.5)
        self._accept_thread = None
        self._emit("VISA bridge stopped")

    def _accept_loop(self) -> None:
        listener = self._listener
        if listener is None:
            return

        while not self._stop.is_set():
            try:
                client, address = listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            if not self._session_lock.acquire(blocking=False):
                self._emit(f"Rejected extra client {address[0]}:{address[1]}")
                self._close_socket(client)
                continue

            threading.Thread(
                target=self._handle_client,
                args=(client, address),
                name="instrument-visa-bridge-session",
                daemon=True,
            ).start()

    def _handle_client(
        self,
        client: socket.socket,
        address: tuple[str, int],
    ) -> None:
        transport: VisaTransport | None = None
        client_text = f"{address[0]}:{address[1]}"
        framer = ScpiLineFramer()
        try:
            self._client = client
            client.settimeout(0.5)
            self.stats.client_connected(client_text)
            self._emit(f"Client connected: {client_text}")

            transport = VisaTransport(
                TransportConfig(
                    resource=self.config.resource,
                    timeout_ms=self.config.timeout_ms,
                    read_termination=None,
                    write_termination=None,
                ),
                backend=self.config.backend or None,
            )
            transport.open()
            self._emit(f"VISA session opened: {self.config.resource}")

            while not self._stop.is_set():
                try:
                    data = client.recv(self.config.recv_size)
                except socket.timeout:
                    continue
                if not data:
                    break

                self.stats.add_from_client(len(data))
                for message in framer.feed(data):
                    transport.write_raw(message)
                    self._emit_scpi("TX", message)
                    if is_scpi_query(message):
                        response = transport.read_raw()
                        client.sendall(response)
                        self.stats.add_to_client(len(response))
                        self._emit(
                            f"RX {len(response)} bytes from VISA instrument"
                        )
        except Exception as exc:
            if not self._stop.is_set():
                self._emit(f"VISA bridge session error: {exc}")
        finally:
            if framer.pending_bytes:
                self._emit(
                    f"Dropped {framer.pending_bytes} unterminated request bytes"
                )
            if transport is not None:
                transport.close()
            self._close_socket(client)
            self._client = None
            self.stats.client_disconnected()
            self._emit(f"Client disconnected: {client_text}")
            self._session_lock.release()

    def _emit_scpi(self, prefix: str, payload: bytes) -> None:
        preview = payload[:160].decode("ascii", errors="replace").strip()
        if len(payload) > 160:
            preview += " ..."
        self._emit(f"{prefix} {preview}")

    def _emit(self, message: str) -> None:
        if self._on_event is not None:
            try:
                self._on_event(message)
            except Exception:
                pass

    @staticmethod
    def _close_socket(sock: socket.socket | None) -> None:
        if sock is None:
            return
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            sock.close()
        except OSError:
            pass
