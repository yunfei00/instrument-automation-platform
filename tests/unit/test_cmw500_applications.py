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
        str(
            ROOT
            / "packages"
            / package
            / "src"
        ),
    )


from instrument_core.transport import (
    MockTransport,
)
from instrument_drivers.rohde_schwarz.cmw500 import (
    RohdeSchwarzCMW500Driver,
)


def main():

    transport = MockTransport()

    driver = (
        RohdeSchwarzCMW500Driver(
            transport
        )
    )

    transport.queue_response(
        "BASE,3.5.120;"
        "LTE,3.5.50;"
        "WCDMA,3.5.40;"
        "GSM,3.5.30;"
        "WLAN,3.5.40;"
        "Bluetooth,3.5.60\n"
    )

    registry = (
        driver
        .get_application_registry()
    )

    assert registry.has("base")
    assert registry.has("lte")
    assert registry.has("wcdma")
    assert registry.has("gsm")
    assert registry.has("wlan")
    assert registry.has("bluetooth")

    assert (
        registry.get(
            "lte"
        ).version
        == "3.5.50"
    )

    assert (
        registry.get(
            "wlan"
        ).measurement
        is True
    )

    assert (
        registry.get(
            "bluetooth"
        ).signaling
        is True
    )

    print(
        "CMW500 application registry test PASS"
    )

    for application in registry.all():
        print(
            application.id,
            application.version,
        )


if __name__ == "__main__":
    main()
