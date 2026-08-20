import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(
    0,
    str(ROOT / "packages/instrument_core/src"),
)

sys.path.insert(
    0,
    str(ROOT / "packages/instrument_scpi/src"),
)

from instrument_core.transport import MockTransport
from instrument_scpi import SCPIClient, parse_definite_length_block


def test_idn():
    transport = MockTransport()
    transport.open()

    transport.queue_response(
        "KEYSIGHT TECHNOLOGIES,DSO-X 3034A,MY123456,02.50\n"
    )

    client = SCPIClient(transport)
    identity = client.identify()

    assert identity.manufacturer == "KEYSIGHT TECHNOLOGIES"
    assert identity.model == "DSO-X 3034A"
    assert identity.serial_number == "MY123456"
    assert identity.firmware == "02.50"
    assert transport.writes == ["*IDN?"]


def test_binary_block():
    data = b"#210abcdefghij\n"

    block = parse_definite_length_block(data)

    assert block.header == b"#210"
    assert block.payload == b"abcdefghij"
    assert block.trailing == b"\n"


def test_scpi_error():
    transport = MockTransport()
    transport.open()

    transport.queue_response('-113,"Undefined header"\n')

    client = SCPIClient(transport)

    code, message = client.query_error()

    assert code == -113
    assert message == "Undefined header"
