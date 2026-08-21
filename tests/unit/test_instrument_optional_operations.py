import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(
    0,
    str(
        ROOT
        / "packages"
        / "instrument_core"
        / "src"
    ),
)


from instrument_core import (
    CapabilitySet,
    InstrumentDriver,
)
from instrument_core.errors import (
    UnsupportedCapabilityError,
)
from instrument_core.models import (
    InstrumentIdentity,
)
from instrument_core.transport import (
    MockTransport,
)


class MinimalInstrument(
    InstrumentDriver
):
    @property
    def capabilities(self):
        return CapabilitySet()

    def identify(self):
        return InstrumentIdentity(
            manufacturer="TEST",
            model="MODULAR",
            serial_number="1",
            firmware="1.0",
            raw="TEST,MODULAR,1,1.0",
        )

    def health_check(self):
        return True

    def get_errors(self):
        return []

    def clear_errors(self):
        return None


def assert_unsupported(
    callback,
):
    try:
        callback()
    except UnsupportedCapabilityError:
        pass
    else:
        raise AssertionError(
            "Expected UnsupportedCapabilityError"
        )


def main():

    transport = MockTransport()

    driver = MinimalInstrument(
        transport
    )

    identity = driver.connect()

    assert identity.model == "MODULAR"

    assert_unsupported(
        driver.reset
    )

    assert_unsupported(
        driver.abort
    )

    assert_unsupported(
        driver.remote
    )

    assert_unsupported(
        driver.local
    )

    # disconnect must not call local because
    # REMOTE_LOCAL is not advertised.
    driver.disconnect()

    assert not driver.is_connected

    print(
        "Optional instrument operations test PASS"
    )


if __name__ == "__main__":
    main()
