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
from instrument_drivers.registry import (
    driver_registry,
)
from instrument_drivers.rohde_schwarz.cmw500 import (
    RohdeSchwarzCMW500Driver,
    parse_software_versions,
    parse_subinstrument_info,
)


def main():

    sub = parse_subinstrument_info(
        "0,2"
    )

    assert sub.current_index == 0
    assert sub.current_number == 1
    assert sub.count == 2

    packages = (
        parse_software_versions(
            "BASE,3.7.10;"
            "LTE,3.7.10;"
            "WCDMA,3.7.10"
        )
    )

    assert len(packages) == 3

    assert (
        packages[0].name
        == "BASE"
    )

    assert (
        packages[1].version
        == "3.7.10"
    )

    transport = MockTransport()

    driver = (
        RohdeSchwarzCMW500Driver(
            transport
        )
    )

    transport.queue_response(
        "Rohde&Schwarz,"
        "CMW,"
        "1201.0002K50/123456,"
        "3.7.10\n"
    )

    identity = (
        driver.connect()
    )

    assert identity.model == "CMW"

    transport.queue_response(
        "'1201.0002K50/123456'\n"
    )

    assert (
        driver.get_device_id()
        == "1201.0002K50/123456"
    )

    transport.queue_response(
        "CMW-B110,CMW-B120,"
        "CMW-KM050\n"
    )

    options = (
        driver
        .get_installed_options_raw()
    )

    assert "CMW-B110" in options

    transport.queue_response(
        "BASE,3.7.10;"
        "LTE,3.7.10;"
        "WCDMA,3.7.10\n"
    )

    versions = (
        driver.get_software_versions()
    )

    assert len(versions) == 3

    transport.queue_response(
        "0,2\n"
    )

    info = (
        driver
        .get_subinstrument_info()
    )

    assert info.count == 2

    transport.queue_response(
        "'TCPIP0::10.0.0.1::"
        "hislip0::INSTR'\n"
    )

    assert (
        driver
        .get_hislip_resource(1)
        == (
            "TCPIP0::10.0.0.1::"
            "hislip0::INSTR"
        )
    )

    transport.queue_response(
        "'TCPIP0::10.0.0.1::"
        "inst0::INSTR'\n"
    )

    assert (
        driver
        .get_vxi_resource(1)
        == (
            "TCPIP0::10.0.0.1::"
            "inst0::INSTR"
        )
    )

    transport.queue_response(
        "'USB0::0x0AAD::"
        "0x57::123456::INSTR'\n"
    )

    assert (
        "USB0::"
        in driver.get_usb_resource()
    )

    descriptor = (
        driver_registry.find(
            "Rohde&Schwarz",
            "CMW",
        )
    )

    assert (
        descriptor.family
        == "CMW500"
    )

    assert (
        descriptor.driver_class
        is RohdeSchwarzCMW500Driver
    )

    driver.disconnect()

    print(
        "CMW500 base driver self-test PASS"
    )


if __name__ == "__main__":
    main()
