"""Base contract for all instrument drivers."""

from abc import ABC, abstractmethod

from .capabilities import (
    Capability,
    CapabilitySet,
)
from .errors import (
    UnsupportedCapabilityError,
)
from .models import (
    InstrumentIdentity,
    InstrumentState,
)
from .transport import Transport


class InstrumentDriver(ABC):
    """
    Base contract for production instrument drivers.

    Only universally meaningful behavior is abstract.

    Device-specific operational behavior such as reset, abort,
    remote/local switching may be unsupported by an instrument
    or may belong to a more specific subsystem such as a
    measurement application.
    """

    def __init__(
        self,
        transport: Transport,
    ):
        self.transport = transport

        self._state = (
            InstrumentState.DISCONNECTED
        )

        self._identity: (
            InstrumentIdentity | None
        ) = None

    @property
    def state(
        self,
    ) -> InstrumentState:
        return self._state

    @property
    def identity(
        self,
    ) -> InstrumentIdentity | None:
        return self._identity

    @property
    def is_connected(
        self,
    ) -> bool:
        return self.transport.is_open

    @property
    @abstractmethod
    def capabilities(
        self,
    ) -> CapabilitySet:
        """Return capabilities supported by this device."""

    def supports(
        self,
        capability: Capability,
    ) -> bool:
        return self.capabilities.supports(
            capability
        )

    def connect(
        self,
    ) -> InstrumentIdentity:

        self._state = (
            InstrumentState.CONNECTING
        )

        try:
            self.transport.open()

            self._state = (
                InstrumentState.CONNECTED
            )

            identity = self.identify()

            self._identity = identity

            self._state = (
                InstrumentState.READY
            )

            return identity

        except Exception:
            self._state = (
                InstrumentState.ERROR
            )

            try:
                self.transport.close()
            except Exception:
                pass

            raise

    def disconnect(self) -> None:

        try:
            if (
                self.transport.is_open
                and self.supports(
                    Capability.REMOTE_LOCAL
                )
            ):
                try:
                    self.local()
                except Exception:
                    pass

        finally:
            self.transport.close()

            self._state = (
                InstrumentState.DISCONNECTED
            )

    @abstractmethod
    def identify(
        self,
    ) -> InstrumentIdentity:
        """Identify the connected instrument."""

    @abstractmethod
    def health_check(
        self,
    ) -> bool:
        """Check whether the instrument is responsive."""

    @abstractmethod
    def get_errors(
        self,
    ) -> list[tuple[int, str]]:
        """Return current instrument errors."""

    @abstractmethod
    def clear_errors(
        self,
    ) -> None:
        """Clear instrument error/status state."""

    def reset(self) -> None:
        """
        Reset the instrument when supported.

        Override in drivers with a meaningful device-level reset.
        """
        raise UnsupportedCapabilityError(
            "Instrument does not provide "
            "a generic reset operation"
        )

    def abort(self) -> None:
        """
        Abort the current operation when meaningful.

        Some modular instruments only support abort at an
        application or measurement level.
        """
        raise UnsupportedCapabilityError(
            "Instrument does not provide "
            "a generic abort operation"
        )

    def remote(self) -> None:
        """Enter explicit remote mode when supported."""
        raise UnsupportedCapabilityError(
            "Instrument does not provide "
            "explicit remote-mode control"
        )

    def local(self) -> None:
        """Return to local/front-panel mode when supported."""
        raise UnsupportedCapabilityError(
            "Instrument does not provide "
            "explicit local-mode control"
        )
