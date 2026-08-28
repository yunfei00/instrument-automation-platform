"""Transport package public exports with lazy loading."""

from importlib import import_module


_EXPORTS = {
    "Transport": (".base", "Transport"),
    "TransportConfig": (".base", "TransportConfig"),
    "MockTransport": (".mock", "MockTransport"),
    "VisaTransport": (".visa", "VisaTransport"),
    "RecordingTransport": (".recording", "RecordingTransport"),
    "ReplayTransport": (".replay", "ReplayTransport"),
    "ReplayMismatchError": (".replay", "ReplayMismatchError"),
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
