"""PyVISA based instrument transport."""

from typing import Any

from instrument_core.errors import (
    InstrumentConnectionError,
    InstrumentTimeoutError,
    TransportError,
)

from .base import Transport, TransportConfig


class VisaTransport(Transport):
    """VISA implementation of the common Transport interface."""

    def __init__(self, config: TransportConfig, backend: str | None = None):
        super().__init__(config)
        self.backend = backend
        self._resource_manager: Any = None
        self._resource: Any = None

    @property
    def is_open(self) -> bool:
        return self._resource is not None

    def open(self) -> None:
        try:
            import pyvisa

            if self.backend:
                self._resource_manager = pyvisa.ResourceManager(self.backend)
            else:
                self._resource_manager = pyvisa.ResourceManager()

            self._resource = self._resource_manager.open_resource(
                self.config.resource
            )

            self._resource.timeout = self.config.timeout_ms

            if self.config.read_termination is not None:
                self._resource.read_termination = (
                    self.config.read_termination
                )

            if self.config.write_termination is not None:
                self._resource.write_termination = (
                    self.config.write_termination
                )

        except Exception as exc:
            self._resource = None
            raise InstrumentConnectionError(
                f"Failed to open VISA resource "
                f"{self.config.resource}: {exc}"
            ) from exc

    def close(self) -> None:
        if self._resource is not None:
            try:
                self._resource.close()
            finally:
                self._resource = None

        if self._resource_manager is not None:
            try:
                self._resource_manager.close()
            finally:
                self._resource_manager = None

    def _require_resource(self):
        if self._resource is None:
            raise InstrumentConnectionError(
                "VISA resource is not open"
            )
        return self._resource

    def _translate_error(self, exc: Exception):
        text = str(exc).lower()

        if "timeout" in text:
            return InstrumentTimeoutError(str(exc))

        return TransportError(str(exc))

    def write(self, command: str) -> None:
        resource = self._require_resource()

        try:
            resource.write(command)
        except Exception as exc:
            raise self._translate_error(exc) from exc

    def read(self) -> str:
        resource = self._require_resource()

        try:
            return resource.read()
        except Exception as exc:
            raise self._translate_error(exc) from exc

    def write_raw(self, data: bytes) -> None:
        resource = self._require_resource()

        try:
            resource.write_raw(data)
        except Exception as exc:
            raise self._translate_error(exc) from exc

    def read_raw(self) -> bytes:
        resource = self._require_resource()

        try:
            return resource.read_raw()
        except Exception as exc:
            raise self._translate_error(exc) from exc

    def clear(self) -> None:
        resource = self._require_resource()

        try:
            resource.clear()
        except Exception as exc:
            raise self._translate_error(exc) from exc
