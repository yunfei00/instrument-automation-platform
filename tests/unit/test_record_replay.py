import struct
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

for package in [
    "instrument_core",
    "instrument_scpi",
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
    RecordingTransport,
    ReplayMismatchError,
    ReplayTransport,
)
from instrument_scpi import SCPIClient


def create_session(
    path: Path,
):
    mock = MockTransport()

    mock.queue_response(
        "KEYSIGHT TECHNOLOGIES,"
        "DSO-X 3034A,"
        "MY123456,"
        "02.50\n"
    )

    mock.queue_response(
        "1.000000E-04\n"
    )

    payload = struct.pack(
        "<4h",
        0,
        100,
        -100,
        200,
    )

    raw_response = (
        b"#1"
        + str(
            len(payload)
        ).encode("ascii")
        + payload
        + b"\n"
    )

    mock.queue_raw_response(
        raw_response
    )

    recording = RecordingTransport(
        mock,
        path,
    )

    recording.open()

    client = SCPIClient(
        recording
    )

    identity = (
        client.identify()
    )

    assert (
        identity.model
        == "DSO-X 3034A"
    )

    scale = float(
        client.query(
            ":TIMebase:SCALe?"
        )
    )

    assert scale == 1e-4

    raw = recording.query_raw(
        ":WAVeform:DATA?"
    )

    assert raw == raw_response

    recording.close()


def replay_session(
    path: Path,
):
    replay = ReplayTransport(
        path
    )

    replay.open()

    client = SCPIClient(
        replay
    )

    identity = (
        client.identify()
    )

    assert (
        identity.model
        == "DSO-X 3034A"
    )

    scale = float(
        client.query(
            ":TIMebase:SCALe?"
        )
    )

    assert scale == 1e-4

    raw = replay.query_raw(
        ":WAVeform:DATA?"
    )

    assert raw.startswith(
        b"#1"
    )

    replay.close()

    replay.assert_complete()


def assert_mismatch(
    path: Path,
):
    replay = ReplayTransport(
        path
    )

    replay.open()

    try:
        replay.write(
            "*RST"
        )
    except ReplayMismatchError:
        pass
    else:
        raise AssertionError(
            "Replay mismatch was not detected"
        )


def test_mismatch(
    tmp_path: Path,
):
    session_path = (
        tmp_path
        / "session.jsonl"
    )

    create_session(
        session_path
    )

    assert_mismatch(
        session_path
    )


def main():
    with tempfile.TemporaryDirectory() as temp:
        session_path = (
            Path(temp)
            / "session.jsonl"
        )

        create_session(
            session_path
        )

        assert (
            session_path.exists()
        )

        assert (
            session_path.stat().st_size
            > 0
        )

        replay_session(
            session_path
        )

        assert_mismatch(
            session_path
        )

    print(
        "Record / Replay self-test PASS"
    )


if __name__ == "__main__":
    main()
