import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

for package in [
    "instrument_core",
    "instrument_scpi",
    "instrument_drivers",
]:
    sys.path.insert(
        0,
        str(ROOT / f"packages/{package}/src"),
    )

from instrument_core import (
    Capability,
    CapabilitySet,
    InstrumentDriver,
    InstrumentIdentity,
)
from instrument_core.transport import MockTransport
from instrument_drivers import (
    DriverDescriptor,
    DriverRegistry,
)


class DummyDriver(InstrumentDriver):

    @property
    def capabilities(self):
        return CapabilitySet.from_values(
            Capability.WAVEFORM,
            Capability.TRIGGER,
        )

    def identify(self):
        return InstrumentIdentity(
            manufacturer="KEYSIGHT TECHNOLOGIES",
            model="DSO-X 3034A",
        )

    def reset(self):
        pass

    def health_check(self):
        return True

    def get_errors(self):
        return []

    def clear_errors(self):
        pass

    def abort(self):
        pass

    def remote(self):
        pass

    def local(self):
        pass


def test_capabilities():
    capabilities = CapabilitySet.from_values(
        Capability.WAVEFORM,
        Capability.TRIGGER,
    )

    assert capabilities.supports(
        Capability.WAVEFORM
    )

    assert not capabilities.supports(
        Capability.SPECTRUM
    )


def test_driver_lifecycle():
    transport = MockTransport()
    driver = DummyDriver(transport)

    identity = driver.connect()

    assert driver.is_connected
    assert identity.model == "DSO-X 3034A"

    driver.disconnect()

    assert not driver.is_connected


def test_driver_registry():
    registry = DriverRegistry()

    descriptor = DriverDescriptor(
        manufacturer="KEYSIGHT",
        family="DSOX3000",
        models=("DSO-X 30*",),
        driver_class=DummyDriver,
    )

    registry.register(descriptor)

    result = registry.find(
        "KEYSIGHT TECHNOLOGIES",
        "DSO-X 3034A",
    )

    assert result.family == "DSOX3000"
    assert result.driver_class is DummyDriver
