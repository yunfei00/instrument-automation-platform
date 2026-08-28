"""Public exports for the instrument automation core.

The package uses lazy attribute loading so lightweight tools can import a small
submodule (for example ``instrument_core.bridge``) without importing every
optional transport/driver dependency.  This also keeps the bridge runtime
compatible with Python 3.8 for legacy instrument PCs.
"""

from importlib import import_module


_EXPORTS = {
    "Capability": (".capabilities", "Capability"),
    "CapabilitySet": (".capabilities", "CapabilitySet"),
    "InstrumentDriver": (".instrument", "InstrumentDriver"),
    "InstrumentIdentity": (".models", "InstrumentIdentity"),
    "InstrumentState": (".models", "InstrumentState"),
    "InstrumentError": (".errors", "InstrumentError"),
    "TransportError": (".errors", "TransportError"),
    "InstrumentConnectionError": (".errors", "InstrumentConnectionError"),
    "InstrumentDisconnectedError": (".errors", "InstrumentDisconnectedError"),
    "InstrumentTimeoutError": (".errors", "InstrumentTimeoutError"),
    "OperationCanceledError": (".errors", "OperationCanceledError"),
    "ProtocolError": (".errors", "ProtocolError"),
    "SCPIError": (".errors", "SCPIError"),
    "DataIntegrityError": (".errors", "DataIntegrityError"),
    "UnsupportedCapabilityError": (".errors", "UnsupportedCapabilityError"),
    "InstrumentBusyError": (".errors", "InstrumentBusyError"),
    "TriggerTimeoutError": (".errors", "TriggerTimeoutError"),
    "CalibrationError": (".errors", "CalibrationError"),
    "Transport": (".transport", "Transport"),
    "TransportConfig": (".transport", "TransportConfig"),
    "MockTransport": (".transport", "MockTransport"),
    "VisaTransport": (".transport", "VisaTransport"),
    "RecordingTransport": (".transport", "RecordingTransport"),
    "ReplayTransport": (".transport", "ReplayTransport"),
    "ReplayMismatchError": (".transport", "ReplayMismatchError"),
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError("module %r has no attribute %r" % (__name__, name)) from exc

    value = getattr(import_module(module_name, __name__), attribute_name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
