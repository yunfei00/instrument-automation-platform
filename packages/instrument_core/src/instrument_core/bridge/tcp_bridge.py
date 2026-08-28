"""Raw TCP-to-TCP instrument bridge."""

from __future__ import annotations

import socket
import threading
from typing import Callable

from .models import BridgeStats, BridgeStatsSnapshot, TcpBridgeConfig

EventCallback = Callable[[str], None]


class TcpBridgeServer:
    """Expose a remote TCP instrument through a local TCP listening port.

    The first connected client owns the instrument session.  Additional
    clients are rejected until that session disconnects, preventing SCPI
    request/response streams from being interleaved.
    """

    def __init__(
        self,
        config: TcpBridgeConfig,
        *,
        on_event: EventCallback | None = None,
    ) -> None:
        config.validate()
        self.config = config
        self._on_event = on_event
        self._stop = threading.Event()
        self._listener: socket.socket | None = None
        self._client: socket.socket | None = None
        self._upstream: socket.socket | None = None
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
            name="instrument-tcp-bridge-accept",
            daemon=True,
        )
        self._accept_thread.start()
        self._emit(
            f"TCP bridge listening on {self.config.listen_host}:"
            f"{self.config.listen_port} -> {self.config.remote_host}:"
            f"{self.config.remote_port}"
        )

    def stop(self) -> None:
        self._stop.set()
        self._close_socket(self._listener)
        self._close_socket(self._client)
        self._close_socket(self._upstream)
        self._listener = None
        self._client = None
        self._upstream = None
        self.stats.client_disconnected()
        self.stats.set_running(False)

        thread = self._accept_thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1.5)
        self._accept_thread = None
        self._emit("TCP bridge stopped")

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
                name="instrument-tcp-bridge-session",
                daemon=True,
            ).start()

    def _handle_client(
        self,
        client: socket.socket,
        address: tuple[str, int],
    ) -> None:
        upstream: socket.socket | None = None
        client_text = f"{address[0]}:{address[1]}"
        try:
            self._client = client
            self.stats.client_connected(client_text)
            self._emit(f"Client connected: {client_text}")

            upstream = socket.create_connection(
                (self.config.remote_host, self.config.remote_port),
                timeout=self.config.connect_timeout_s,
            )
            upstream.settimeout(None)
            client.settimeout(None)
            self._upstream = upstream
            self._emit("Connected to remote instrument")

            done = threading.Event()
            left = threading.Thread(
                target=self._pump,
                args=(client, upstream, True, done),
                name="instrument-tcp-client-to-instrument",
                daemon=True,
            )
            right = threading.Thread(
                target=self._pump,
                args=(upstream, client, False, done),
                name="instrument-tcp-instrument-to-client",
                daemon=True,
            )
            left.start()
            right.start()
            done.wait()
        except Exception as exc:
            self._emit(f"TCP bridge session error: {exc}")
        finally:
            self._close_socket(client)
            self._close_socket(upstream)
            self._client = None
            self._upstream = None
            self.stats.client_disconnected()
            self._emit(f"Client disconnected: {client_text}")
            self._session_lock.release()

    def _pump(
        self,
        source: socket.socket,
        target: socket.socket,
        from_client: bool,
        done: threading.Event,
    ) -> None:
        try:
            while not self._stop.is_set() and not done.is_set():
                data = source.recv(self.config.recv_size)
                if not data:
                    break
                target.sendall(data)
                if from_client:
                    self.stats.add_from_client(len(data))
                else:
                    self.stats.add_to_client(len(data))
        except OSError as exc:
            if not self._stop.is_set():
                self._emit(f"TCP stream closed: {exc}")
        finally:
            done.set()
            try:
                source.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                target.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

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
