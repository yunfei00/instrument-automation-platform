"""Common exception hierarchy for instrument automation."""

class InstrumentError(Exception):
    """Base exception for all platform instrument errors."""


class TransportError(InstrumentError):
    """Base transport communication error."""


class InstrumentConnectionError(TransportError):
    """Instrument connection could not be established."""


class InstrumentDisconnectedError(TransportError):
    """Instrument connection was lost."""


class InstrumentTimeoutError(TransportError):
    """Instrument communication timed out."""


class ProtocolError(InstrumentError):
    """Instrument protocol response was invalid."""


class SCPIError(ProtocolError):
    """Instrument reported a SCPI error."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"SCPI error {code}: {message}")


class DataIntegrityError(InstrumentError):
    """Returned instrument data failed validation."""


class UnsupportedCapabilityError(InstrumentError):
    """Requested capability is not supported by the instrument."""


class InstrumentBusyError(InstrumentError):
    """Instrument is temporarily busy."""


class OperationCanceledError(InstrumentError):
    """Instrument operation was canceled by the caller."""


class TriggerTimeoutError(InstrumentTimeoutError):
    """Instrument did not complete trigger/acquisition in time."""


class CalibrationError(InstrumentError):
    """Instrument is calibrating or calibration failed."""
